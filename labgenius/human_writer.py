"""
Autonomous Human Writer & Academic De-Roboticization Engine for LabGenius.
Provides document structure analysis, cover page detection & preservation,
AI authenticity detection, profile-driven prose humanization, code-reference scrubbing,
and metadata sanitization.
"""

import os
import re
import math
import shutil
import tempfile
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import docx
from pypdf import PdfReader, PdfWriter

from .config import Config
from .doc_tools import _run_libreoffice_convert


@dataclass
class DocumentSegment:
    """Represents a discrete structural unit (paragraph, heading, cover element)."""
    id: int
    type: str  # 'cover', 'heading', 'paragraph', 'code', 'table'
    text: str
    ai_score: float = 0.0  # 0.0 (Human) to 1.0 (Blatant AI)
    is_ai: bool = False
    is_cover_page: bool = False
    reasons: List[str] = field(default_factory=list)
    humanized_text: Optional[str] = None
    code_references: List[str] = field(default_factory=list)


@dataclass
class HumanWriterAnalysis:
    """Full document analysis report."""
    filename: str
    total_words: int
    total_paragraphs: int
    cover_page_detected: bool
    overall_ai_score: float  # Percentage 0.0 to 100.0%
    classification: str     # 'Likely AI-Generated', 'Mixed Content', 'Authentic Human'
    segments: List[DocumentSegment]
    code_references_found: List[str]


class AIDetector:
    """Detects robotic AI mannerisms, low burstiness, and code/variable leaks."""

    # Hallmarks of modern AI models (ChatGPT, Claude, Gemini boilerplate)
    BANNED_AI_MARKERS = {
        r"\bdelve(?:s|d|ing)?\b": "delve phrasing",
        r"\bpivotal\b": "formulaic 'pivotal'",
        r"\bcrucial role\b": "cliché 'crucial role'",
        r"\bserves as a testament\b": "formulaic 'testament'",
        r"\bmeticulous(?:ly)?\b": "formulaic 'meticulous'",
        r"\bcomprehensive understanding\b": "generic academic filler",
        r"\bit is important to note that\b": "redundant AI hedging",
        r"\bit is worth noting that\b": "redundant AI hedging",
        r"\bit is crucial to (?:understand|note|recognize)\b": "redundant AI hedging",
        r"\bin conclusion,?\s+(?:it can be (?:seen|observed)|we can see)\b": "robotic transition",
        r"\bfurthermore,?\s+": "repetitive 'furthermore'",
        r"\bmoreover,?\s+": "repetitive 'moreover'",
        r"\bconsequently,?\s+": "formulaic 'consequently'",
        r"\bas an ai\b": "direct AI self-reference",
        r"\blanguage model\b": "direct AI self-reference",
        r"\bharness(?:ing)? the power of\b": "formulaic 'harness the power'",
        r"\bseamless(?:ly)?\b": "cliché 'seamlessly'",
        r"\bmultifaceted\b": "formulaic 'multifaceted'",
        r"\bparamount\b": "formulaic 'paramount'",
        r"\bin the realm of\b": "cliché 'in the realm of'",
        r"\bserves as an indispensable\b": "overly formal filler",
        r"\bnoteworthy that\b": "formulaic 'noteworthy'",
        r"\butilizes?\b": "pompous 'utilize'",
        r"\butilizing\b": "pompous 'utilizing'",
        r"\ba testament to the\b": "cliché 'testament to'",
        r"\bfosters? an environment\b": "corporate AI filler",
        r"\bintricate tapestry\b": "overt AI metaphor",
        r"\bbeacon of\b": "overt AI metaphor",
        r"\bunderlying principles of\b": "robotic academic filler",
        r"\bdemonstrates the efficacy of\b": "robotic academic filler",
    }

    # Code reference patterns leaking into prose
    CODE_LEAK_PATTERNS = [
        r"`([a-zA-Z0-9_]{3,35})`",                          # Backticked identifiers
        r"\b(?:variable|function|method|dataframe|query)\s+([a-zA-Z0-9_]{3,35})\b",
        r"\b[a-z]{2,8}_(?:v\d+|sol|task|final|cleaned|res|df|val|arr|idx)\b", # Variable signatures
        r"\b(?:task_\d+_(?:sol|solution|code)|prompt_v\d+)\b",
    ]

    @classmethod
    def analyze_burstiness(cls, text: str) -> Tuple[float, float]:
        """
        Calculates mean sentence length and variance (burstiness).
        Human writing has high variance (mix of punchy and elaborate sentences).
        AI text typically has uniform, mid-length sentences.
        """
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 3]
        if len(sentences) < 2:
            return 15.0, 5.0  # Neutral baseline
        lengths = [len(s.split()) for s in sentences]
        mean_len = sum(lengths) / len(lengths)
        variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
        std_dev = math.sqrt(variance)
        return mean_len, std_dev

    @classmethod
    def detect_code_references(cls, text: str) -> List[str]:
        """Finds raw code variables or internal script tokens in text."""
        leaks = []
        for pat in cls.CODE_LEAK_PATTERNS:
            matches = re.findall(pat, text, flags=re.IGNORECASE)
            for m in matches:
                token = m if isinstance(m, str) else m[0]
                if token and len(token) > 2 and token not in leaks:
                    leaks.append(token)
        return leaks

    @classmethod
    def evaluate_text(cls, text: str) -> Tuple[float, List[str], List[str]]:
        """
        Evaluates a segment of text and returns:
        (ai_probability [0.0-1.0], reasons_list, code_references_list)
        """
        clean = text.strip()
        if not clean or len(clean.split()) < 5:
            return 0.05, [], []

        reasons = []
        marker_hits = 0

        # 1. Banned AI markers
        for pat, desc in cls.BANNED_AI_MARKERS.items():
            found = re.findall(pat, clean, flags=re.IGNORECASE)
            if found:
                marker_hits += len(found)
                reasons.append(f"{desc} ('{found[0]}')")

        # 2. Code references in prose
        code_refs = cls.detect_code_references(clean)
        if code_refs:
            reasons.append(f"Leaked code/variable references: {', '.join(code_refs[:3])}")

        # 3. Burstiness evaluation
        words_count = len(clean.split())
        mean_len, std_dev = cls.analyze_burstiness(clean)

        burstiness_penalty = 0.0
        if words_count > 30:
            if std_dev < 3.2:
                burstiness_penalty = 0.25
                reasons.append("Unnaturally uniform sentence rhythm (low burstiness)")
            elif std_dev < 4.5:
                burstiness_penalty = 0.12

        # 4. Synthesizing AI probability score
        words_factor = max(1, words_count / 20.0)
        marker_score = min(0.70, (marker_hits / words_factor) * 0.40)
        code_score = min(0.25, len(code_refs) * 0.10)

        raw_score = marker_score + code_score + burstiness_penalty

        # Clamp between 0.05 and 0.98
        final_score = max(0.05, min(0.98, raw_score))
        return round(final_score, 2), reasons, code_refs


class CoverPageDetector:
    """Detects academic title blocks and cover page elements to protect them."""

    COVER_KEYWORDS = [
        r"\bstudent\s*name\b",
        r"\broll\s*(?:no|number)\b",
        r"\bdepartment\s*of\b",
        r"\bfaculty\s*of\b",
        r"\buniversity\b",
        r"\binstitute\b",
        r"\bcourse\s*(?:title|name|code)\b",
        r"\blab\s*(?:report|manual|assignment|session)\b",
        r"\bsubmitted\s*by\b",
        r"\bsubmitted\s*to\b",
        r"\binstructor\b",
        r"\bacademic\s*year\b",
        r"\bsemester\b",
        r"\bdate\s*of\s*submission\b",
    ]

    @classmethod
    def is_cover_segment(cls, text: str, segment_index: int, total_segments: int) -> bool:
        """Determines if a segment is part of the cover page."""
        # Cover pages only appear in the first 25% or first 4 segments
        if segment_index > max(3, total_segments * 0.25):
            return False

        lower = text.lower()
        keyword_hits = 0
        for pat in cls.COVER_KEYWORDS:
            if re.search(pat, lower):
                keyword_hits += 1

        # Strong signal: 2 or more cover keywords
        if keyword_hits >= 2:
            return True

        # First segment with typical lab title pattern
        if segment_index == 0 and any(w in lower for w in ["lab report", "experiment", "practical", "assignment"]):
            return True

        return False


class HumanizationEngine:
    """Transforms AI-flagged prose into natural, authentic human academic writing."""

    PROFILES = {
        "academic_student": {
            "name": "Academic Student",
            "description": "Natural college student voice. Clear, direct explanations without chatbot fluff.",
        },
        "de_roboticizer": {
            "name": "De-Roboticizer (Strip Code References)",
            "description": "Aggressively purges variable citations, prompt leakage, and formulaic AI markers.",
        },
        "concise": {
            "name": "Concise & Direct",
            "description": "Trims repetitive introductory filler and academic puffery.",
        },
        "casual_viva": {
            "name": "Casual Technical (Viva Voice)",
            "description": "Conversational active-voice explanation suitable for lab discussions.",
        },
        "research_grade": {
            "name": "Research Grade",
            "description": "Polished academic phrasing without robotic tells.",
        },
    }

    # Deterministic dictionary for smart offline humanization
    REPLACEMENTS = {
        r"\bdelve(?:s|d|ing)?\b": "look",
        r"\bpivotal\b": "important",
        r"\bcrucial role\b": "key part",
        r"\bserves as a testament to\b": "shows",
        r"\bmeticulous(?:ly)?\b": "careful",
        r"\bcomprehensive understanding\b": "clear picture",
        r"\bit is important to note that\b": "note that",
        r"\bit is worth noting that\b": "notice that",
        r"\bit is crucial to (?:understand|note|recognize) that\b": "",
        r"\bin conclusion,?\s+it can be (?:seen|observed) that\b": "overall,",
        r"\bfurthermore,?\s+": "also, ",
        r"\bmoreover,?\s+": "in addition, ",
        r"\bconsequently,?\s+": "so, ",
        r"\bas an ai\b": "",
        r"\blanguage model\b": "",
        r"\bharness(?:ing)? the power of\b": "using",
        r"\bseamless(?:ly)?\b": "smoothly",
        r"\bmultifaceted\b": "varied",
        r"\bparamount\b": "very important",
        r"\bin the realm of\b": "in",
        r"\bserves as an indispensable\b": "is a key",
        r"\bnoteworthy that\b": "noticeable that",
        r"\butilizes?\b": "uses",
        r"\butilizing\b": "using",
        r"\ba testament to the\b": "clear evidence of",
        r"\bfosters? an environment\b": "creates conditions",
        r"\bintricate tapestry\b": "complex setup",
        r"\bbeacon of\b": "example of",
        r"\bunderlying principles of\b": "basics of",
        r"\bdemonstrates the efficacy of\b": "shows how well it works",
    }

    @classmethod
    def strip_code_references_in_prose(cls, text: str) -> str:
        """
        Removes raw code identifiers and backticked variable leaks from prose text.
        e.g., "The function `calculate_loss_v2` executes" -> "The function executes"
        e.g., "In variable df_cleaned_final" -> "In the dataset"
        """
        cleaned = text
        # Remove backticks around simple words
        cleaned = re.sub(r"`([a-zA-Z0-9_]+)`", r"\1", cleaned)

        # Clean variable citations
        cleaned = re.sub(
            r"\b(?:variable|dataframe|df)\s+[a-zA-Z0-9_]{3,30}\b",
            "the data",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"\b(?:function|method)\s+[a-zA-Z0-9_]{3,30}\(\)",
            "the procedure",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"\b(?:task_\d+_(?:sol|solution)|prompt_v\d+)\b",
            "the implementation",
            cleaned,
            flags=re.IGNORECASE,
        )
        return cleaned

    @classmethod
    def humanize_segment_offline(
        cls,
        text: str,
        profile: str = "academic_student",
        custom_instructions: str = "",
    ) -> str:
        """Deterministic offline rule-based humanizer."""
        out = text

        # 1. Strip code/variable leaks if requested or under de_roboticizer
        if profile in ["de_roboticizer", "academic_student", "concise"]:
            out = cls.strip_code_references_in_prose(out)

        # 2. Apply dictionary replacements
        for pat, repl in cls.REPLACEMENTS.items():
            out = re.sub(pat, repl, out, flags=re.IGNORECASE)

        # 3. Profile-specific adjustments
        if profile == "concise":
            # Cut common wordy preambles
            out = re.sub(r"^(?:in this lab|as observed previously|it is evident that),?\s*", "", out, flags=re.IGNORECASE)
        elif profile == "casual_viva":
            out = re.sub(r"\bwe observe that\b", "we can see that", out, flags=re.IGNORECASE)
            out = re.sub(r"\bone can conclude\b", "we found that", out, flags=re.IGNORECASE)

        # 4. Clean extra spaces and punctuation artifacts
        out = re.sub(r"\s{2,}", " ", out)
        out = re.sub(r"\s+([.,;:!?])", r"\1", out)
        out = out.strip()
        return out

    @classmethod
    def humanize_segment_llm(
        cls,
        text: str,
        profile: str,
        custom_instructions: str,
        cfg: Config,
    ) -> str:
        """Uses configured AI provider (Gemini/Groq/OpenAI) to humanize text."""
        prompt = (
            f"You are an expert human academic editor. Rewrite the following AI-generated text to sound like "
            f"it was naturally written by a college student. "
            f"Profile: {profile}.\n"
        )
        if custom_instructions:
            prompt += f"Custom Guidance: {custom_instructions}\n"

        prompt += (
            f"Rules:\n"
            f"1. Strictly eliminate words like 'delve', 'pivotal', 'crucial', 'testament', 'seamlessly'.\n"
            f"2. Remove any internal code references, function signatures, or variable names in explanatory text.\n"
            f"3. Vary sentence length (use a natural mix of short and medium sentences).\n"
            f"4. Do NOT output conversational preambles like 'Here is the rewritten text:'. Just output the humanized text.\n\n"
            f"Text to humanize:\n{text}"
        )

        try:
            if cfg.ai.provider == "gemini" and cfg.ai.api_key:
                from .providers.gemini import GeminiProvider
                prov = GeminiProvider(cfg)
                res = prov.generate(prompt)
                if res and res.strip():
                    return res.strip()
            elif cfg.ai.provider == "groq" and cfg.ai.api_key:
                from groq import Groq
                client = Groq(api_key=cfg.ai.api_key)
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                )
                return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"[!] LLM humanization fallback to offline due to: {e}")

        # Fallback to offline rule-based transform
        return cls.humanize_segment_offline(text, profile, custom_instructions)


class MetadataSanitizer:
    """Sanitizes document metadata in DOCX and PDF files to ensure genuine student author appearance."""

    @classmethod
    def sanitize_docx(cls, doc: docx.Document, student_name: Optional[str] = None, title: Optional[str] = None):
        """Sanitizes Word document metadata."""
        author = student_name or "Student"
        doc_title = title or "Academic Lab Report"
        props = doc.core_properties

        props.author = author
        props.last_modified_by = author
        props.title = doc_title
        props.subject = "Laboratory Practical Submission"
        props.keywords = "Lab Report, Analysis, Results, Academic"
        props.category = "Academic Work"
        props.comments = ""
        props.revision = 3

        # Set realistic timestamps (created 2 days ago, modified 15 minutes ago)
        props.created = datetime.now() - timedelta(days=2, hours=3, minutes=12)
        props.modified = datetime.now() - timedelta(minutes=14)

    @classmethod
    def sanitize_pdf(cls, in_pdf_path: Path, out_pdf_path: Path, student_name: Optional[str] = None, title: Optional[str] = None):
        """Sanitizes PDF document metadata using pypdf."""
        reader = PdfReader(str(in_pdf_path))
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        author = student_name or "Student"
        doc_title = title or "Academic Lab Report"

        # Wipe generator metadata, set genuine Microsoft Word author properties
        clean_metadata = {
            "/Author": author,
            "/Creator": "Microsoft® Word 2019",
            "/Producer": "Microsoft® Word 2019",
            "/Title": doc_title,
            "/Subject": "Academic Lab Report",
            "/CreationDate": (datetime.now() - timedelta(days=2)).strftime("D:%Y%m%d%H%M%S"),
            "/ModDate": datetime.now().strftime("D:%Y%m%d%H%M%S"),
        }
        writer.add_metadata(clean_metadata)

        out_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_pdf_path, "wb") as f:
            writer.write(f)


class HumanWriterService:
    """Orchestrates document reading, analysis, humanization, and export."""

    @classmethod
    def extract_text_segments(cls, file_path: Path) -> List[DocumentSegment]:
        """Extracts text segments from .docx, .pdf, .txt, or .md."""
        ext = file_path.suffix.lower()
        raw_paragraphs: List[str] = []

        if ext == ".docx":
            doc = docx.Document(str(file_path))
            for p in doc.paragraphs:
                txt = p.text.strip()
                if txt:
                    raw_paragraphs.append(txt)
            for table in doc.tables:
                for row in table.rows:
                    row_txt = " | ".join(c.text.strip() for c in row.cells if c.text.strip())
                    if row_txt and row_txt not in raw_paragraphs:
                        raw_paragraphs.append(f"[Table Row] {row_txt}")
        elif ext == ".pdf":
            reader = PdfReader(str(file_path))
            for page in reader.pages:
                txt = page.extract_text() or ""
                paras = [p.strip() for p in txt.split("\n\n") if p.strip()]
                raw_paragraphs.extend(paras)
        elif ext in [".txt", ".md"]:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            raw_paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        else:
            # Attempt LibreOffice conversion for .doc or other formats
            temp_dir = Path(tempfile.mkdtemp(prefix="labgen_hw_convert_"))
            try:
                converted = _run_libreoffice_convert(file_path, "docx", temp_dir)
                if converted and converted.exists():
                    return cls.extract_text_segments(converted)
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

        # Build DocumentSegment list
        segments: List[DocumentSegment] = []
        total_p = len(raw_paragraphs)

        for idx, text in enumerate(raw_paragraphs):
            is_cover = CoverPageDetector.is_cover_segment(text, idx, total_p)
            seg_type = "cover" if is_cover else ("heading" if len(text.split()) < 8 and not text.endswith(".") else "paragraph")
            
            if is_cover:
                seg = DocumentSegment(
                    id=idx + 1,
                    type="cover",
                    text=text,
                    ai_score=0.02,
                    is_ai=False,
                    is_cover_page=True,
                    reasons=["Protected Cover Page / Title Block (Preserved)"],
                    humanized_text=text,
                )
            else:
                score, reasons, code_refs = AIDetector.evaluate_text(text)
                is_ai = score >= 0.40
                seg = DocumentSegment(
                    id=idx + 1,
                    type=seg_type,
                    text=text,
                    ai_score=score,
                    is_ai=is_ai,
                    is_cover_page=False,
                    reasons=reasons,
                    code_references=code_refs,
                )
            segments.append(seg)

        return segments

    @classmethod
    def analyze_document(cls, file_path: Path) -> HumanWriterAnalysis:
        """Performs full document analysis."""
        segments = cls.extract_text_segments(file_path)
        total_words = sum(len(s.text.split()) for s in segments)
        total_p = len(segments)

        cover_detected = any(s.is_cover_page for s in segments)
        body_segments = [s for s in segments if not s.is_cover_page]

        if body_segments:
            overall_score = round((sum(s.ai_score for s in body_segments) / len(body_segments)) * 100, 1)
        else:
            overall_score = 5.0

        if overall_score >= 60.0:
            classification = "Likely AI-Generated"
        elif overall_score >= 35.0:
            classification = "Mixed Content (Contains AI)"
        else:
            classification = "Authentic Human-Written"

        all_code_refs = []
        for s in segments:
            for c in s.code_references:
                if c not in all_code_refs:
                    all_code_refs.append(c)

        return HumanWriterAnalysis(
            filename=file_path.name,
            total_words=total_words,
            total_paragraphs=total_p,
            cover_page_detected=cover_detected,
            overall_ai_score=overall_score,
            classification=classification,
            segments=segments,
            code_references_found=all_code_refs,
        )

    @classmethod
    def humanize_document(
        cls,
        segments_data: List[Dict[str, Any]],
        profile: str = "academic_student",
        custom_instructions: str = "",
        cfg: Optional[Config] = None,
    ) -> Dict[str, Any]:
        """
        Executes humanization across document segments.
        Leaves cover page segments 100% untouched.
        """
        config = cfg or Config.load()
        humanized_segments: List[Dict[str, Any]] = []

        total_words_before = 0
        total_words_after = 0
        code_refs_removed = 0

        for seg_dict in segments_data:
            is_cover = seg_dict.get("is_cover_page", False)
            text = seg_dict.get("text", "")
            is_ai = seg_dict.get("is_ai", False)

            words_orig = len(text.split())
            total_words_before += words_orig

            if is_cover:
                # Strictly protect cover page
                humanized = text
                post_score = 0.02
                reasons = ["Protected Cover Page / Title Block (Preserved)"]
            elif is_ai or seg_dict.get("ai_score", 0.0) >= 0.35:
                # Humanize AI or suspect segment
                if config.ai.api_key:
                    humanized = HumanizationEngine.humanize_segment_llm(
                        text, profile, custom_instructions, config
                    )
                else:
                    humanized = HumanizationEngine.humanize_segment_offline(
                        text, profile, custom_instructions
                    )
                post_score, reasons, _ = AIDetector.evaluate_text(humanized)
                code_refs_removed += len(seg_dict.get("code_references", []))
            else:
                # Human segment left as-is with light polishing
                humanized = HumanizationEngine.strip_code_references_in_prose(text)
                post_score = seg_dict.get("ai_score", 0.05)
                reasons = ["Natural Human Rhythm"]

            words_new = len(humanized.split())
            total_words_after += words_new

            res_dict = dict(seg_dict)
            res_dict["humanized_text"] = humanized
            res_dict["post_ai_score"] = post_score
            res_dict["is_ai_post"] = post_score >= 0.35
            res_dict["reasons_post"] = reasons
            humanized_segments.append(res_dict)

        body_post = [s for s in humanized_segments if not s.get("is_cover_page")]
        if body_post:
            new_overall_ai_score = round(
                (sum(s["post_ai_score"] for s in body_post) / len(body_post)) * 100, 1
            )
        else:
            new_overall_ai_score = 4.0

        return {
            "success": True,
            "profile": profile,
            "humanized_segments": humanized_segments,
            "new_ai_score": new_overall_ai_score,
            "authenticity_score": round(100.0 - new_overall_ai_score, 1),
            "words_before": total_words_before,
            "words_after": total_words_after,
            "code_references_removed": code_refs_removed,
        }

    @classmethod
    def build_exported_document(
        cls,
        segments: List[Dict[str, Any]],
        output_format: str,
        output_path: Path,
        author_name: Optional[str] = None,
        document_title: Optional[str] = None,
    ) -> Path:
        """
        Assembles a cleanly formatted Word (.docx) or PDF document with humanized text
        and sanitized metadata.
        """
        doc = docx.Document()

        # Page setup: Standard Letter/A4 with 1-inch margins
        for section in doc.sections:
            section.top_margin = docx.shared.Inches(1)
            section.bottom_margin = docx.shared.Inches(1)
            section.left_margin = docx.shared.Inches(1)
            section.right_margin = docx.shared.Inches(1)

        title = document_title or "Academic Laboratory Report"
        student = author_name or "Student"

        for seg in segments:
            text = seg.get("humanized_text") or seg.get("text") or ""
            is_cover = seg.get("is_cover_page", False)
            seg_type = seg.get("type", "paragraph")

            if is_cover:
                # Cover page heading / title formatting
                p = doc.add_paragraph()
                p.paragraph_format.space_before = docx.shared.Pt(14)
                p.paragraph_format.space_after = docx.shared.Pt(8)
                run = p.add_run(text)
                run.bold = True
                run.font.size = docx.shared.Pt(14)
                run.font.name = "Calibri"
                run.font.color.rgb = docx.shared.RGBColor(31, 35, 40)
            elif seg_type == "heading":
                p = doc.add_paragraph()
                p.paragraph_format.space_before = docx.shared.Pt(12)
                p.paragraph_format.space_after = docx.shared.Pt(4)
                run = p.add_run(text)
                run.bold = True
                run.font.size = docx.shared.Pt(12)
                run.font.name = "Calibri"
                run.font.color.rgb = docx.shared.RGBColor(15, 23, 42)
            else:
                p = doc.add_paragraph()
                p.paragraph_format.space_before = docx.shared.Pt(0)
                p.paragraph_format.space_after = docx.shared.Pt(6)
                p.paragraph_format.line_spacing = 1.15
                run = p.add_run(text)
                run.font.size = docx.shared.Pt(11)
                run.font.name = "Calibri"
                run.font.color.rgb = docx.shared.RGBColor(36, 41, 47)

        # Sanitize DOCX metadata
        MetadataSanitizer.sanitize_docx(doc, student_name=student, title=title)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_docx = output_path.with_suffix(".docx")
        doc.save(str(temp_docx))

        if output_format.lower() == "docx":
            if temp_docx != output_path:
                shutil.move(temp_docx, output_path)
            return output_path

        # If PDF requested, convert using LibreOffice with isolated user profile, then sanitize PDF metadata
        temp_dir = Path(tempfile.mkdtemp(prefix="labgen_pdf_export_"))
        try:
            converted_pdf = _run_libreoffice_convert(temp_docx, "pdf", temp_dir)
            if not converted_pdf or not converted_pdf.exists():
                raise RuntimeError("Failed to generate PDF from humanized Word document.")
            MetadataSanitizer.sanitize_pdf(converted_pdf, output_path, student_name=student, title=title)
            return output_path
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            if temp_docx.exists() and temp_docx != output_path:
                temp_docx.unlink(missing_ok=True)

    @classmethod
    def get_or_create_sample_doc(cls, out_path: Path) -> Path:
        """Creates an authentic student lab report contaminated with typical AI tells and code leaks for testing."""
        if out_path.exists():
            return out_path

        doc = docx.Document()
        
        # 1. Cover page block (Protected)
        p_cov = doc.add_paragraph()
        run = p_cov.add_run("DEPARTMENT OF COMPUTER SCIENCE & SOFTWARE ENGINEERING\n")
        run.bold = True
        run.font.size = docx.shared.Pt(13)
        run2 = p_cov.add_run("LAB REPORT: ADVANCED OPERATING SYSTEMS & CONCURRENCY\n")
        run2.bold = True
        run2.font.size = docx.shared.Pt(15)
        p_cov.add_run("Course: CS-304 Distributed Systems\n")
        p_cov.add_run("Student Name: Hamza Tariq\n")
        p_cov.add_run("Roll Number: 22-CS-114 | Section: A\n")
        p_cov.add_run("Instructor: Dr. Asim Qureshi\n")
        p_cov.add_run("Date of Submission: October 24, 2026\n")

        # 2. Section 1 (AI dense)
        doc.add_heading("1. Introduction and Theoretical Framework", level=1)
        doc.add_paragraph(
            "In the realm of modern operating systems, process scheduling serves as an indispensable pillar that plays a pivotal role in ensuring optimal CPU utilization. "
            "It is crucial to understand that scheduling algorithms delve into the intricate tapestry of thread priority queues to facilitate the seamless execution of background daemons. "
            "Furthermore, this laboratory experiment serves as a testament to the efficacy of multithreaded mutual exclusion under preemptive kernels."
        )

        # 3. Section 2 (Code leak)
        doc.add_heading("2. Experimental Implementation and Code Analysis", level=1)
        doc.add_paragraph(
            "In our implementation, we observed that variable task_1_sol_thread_count_v2 facilitates synchronization across the shared memory buffer. "
            "It is important to note that function `pthread_mutex_lock_wrapper_v3()` ensures deadlock prevention. "
            "Moreover, the dataframe df_execution_latency_v2 demonstrates the efficacy of the spinlock mechanism under high contention."
        )

        # 4. Section 3 (Robotic conclusion)
        doc.add_heading("3. Analysis Questions & Discussion", level=1)
        doc.add_paragraph(
            "In conclusion, it can be seen that preemptive scheduling harnesses the power of hardware timer interrupts. "
            "Consequently, the meticulously gathered metrics serve as a testament to low latency performance. "
            "As an AI-inspired student architecture, it is worth noting that memory coherence is maintained seamlessly."
        )

        out_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(out_path))
        return out_path
