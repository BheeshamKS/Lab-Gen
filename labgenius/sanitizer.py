"""
Metadata & Anti-Detection Sanitizer for LabGenius.
Rewrites docProps/core.xml and docProps/app.xml in DOCX files to inject realistic human editing
times, matching student author metadata, and purging all traces of automated generators.
"""

import os
import io
import random
import zipfile
import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import xml.etree.ElementTree as ET

from .config import Config


class DocumentSanitizer:
    """Sanitizes document metadata to pass all automated and human inspection checks."""

    def __init__(self, config: Config):
        self.config = config
        self.student = config.student
        self.doc_conf = config.document

    def sanitize_docx(self, docx_path: Path) -> bool:
        """Deeply sanitizes a DOCX file to match human student authorship."""
        if not docx_path.exists():
            return False

        # Generate realistic human timing
        now = datetime.datetime.now(datetime.timezone.utc)
        editing_mins = self.doc_conf.realistic_editing_minutes + random.randint(-12, 18)
        created_time = now - datetime.timedelta(minutes=editing_mins + random.randint(15, 45))
        modified_time = now - datetime.timedelta(minutes=random.randint(5, 15))
        revision = str(self.doc_conf.realistic_revisions + random.randint(-1, 2))

        # Format ISO strings: 2026-09-12T21:42:00Z
        created_str = created_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        modified_str = modified_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        import xml.sax.saxutils as saxutils

        def xesc(s: str) -> str:
            return saxutils.escape(str(s))

        student_name_xml = xesc(self.student.name)
        student_roll_xml = xesc(self.student.roll_number)
        student_dept_xml = xesc(self.student.department)
        student_uni_xml = xesc(self.student.university)
        app_tag_xml = xesc(self.doc_conf.application_tag)

        # Custom humanized core.xml
        core_xml_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:dcterms="http://purl.org/dc/terms/"
  xmlns:dcmitype="http://purl.org/dc/dcmitype/"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Lab Report - {student_dept_xml}</dc:title>
  <dc:subject>{student_roll_xml}</dc:subject>
  <dc:creator>{student_name_xml}</dc:creator>
  <cp:keywords>academic, lab report, data science</cp:keywords>
  <dc:description></dc:description>
  <cp:lastModifiedBy>{student_name_xml}</cp:lastModifiedBy>
  <cp:revision>{revision}</cp:revision>
  <dcterms:created xsi:type="dcterms:W3CDTF">{created_str}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{modified_str}</dcterms:modified>
  <cp:category>Academic Report</cp:category>
</cp:coreProperties>"""

        # Custom humanized app.xml
        app_xml_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
  xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Template>Normal.dotm</Template>
  <TotalTime>{editing_mins}</TotalTime>
  <Pages>3</Pages>
  <Words>840</Words>
  <Characters>4650</Characters>
  <Application>{app_tag_xml}</Application>
  <DocSecurity>0</DocSecurity>
  <Lines>38</Lines>
  <Paragraphs>22</Paragraphs>
  <ScaleCrop>false</ScaleCrop>
  <Company>{student_uni_xml}</Company>
  <LinksUpToDate>false</LinksUpToDate>
  <CharactersWithSpaces>5420</CharactersWithSpaces>
  <SharedDoc>false</SharedDoc>
  <HyperlinksChanged>false</HyperlinksChanged>
  <AppVersion>16.0000</AppVersion>
</Properties>"""

        # Read archive into memory and rewrite
        temp_zip_buf = io.BytesIO()
        with zipfile.ZipFile(docx_path, "r") as zin:
            with zipfile.ZipFile(temp_zip_buf, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    content = zin.read(item.filename)

                    if item.filename == "docProps/core.xml":
                        zout.writestr(item, core_xml_content.encode("utf-8"))
                    elif item.filename == "docProps/app.xml":
                        zout.writestr(item, app_xml_content.encode("utf-8"))
                    else:
                        # Scrub any text containing 'python-docx' from relationships or comments
                        if b"python-docx" in content:
                            content = content.replace(b"python-docx", self.student.name.encode("utf-8"))
                        zout.writestr(item, content)

        # Overwrite original docx file with sanitized archive
        with open(docx_path, "wb") as f:
            f.write(temp_zip_buf.getvalue())

        return True

    def verify_sanitization(self, docx_path: Path) -> Dict[str, Any]:
        """Verify that all AI traces have been scrubbed."""
        results = {
            "creator": None,
            "last_modified_by": None,
            "total_time_mins": None,
            "revision": None,
            "has_python_docx_tag": False,
        }

        try:
            with zipfile.ZipFile(docx_path, "r") as z:
                core_xml = z.read("docProps/core.xml").decode("utf-8", errors="ignore")
                app_xml = z.read("docProps/app.xml").decode("utf-8", errors="ignore")

                # Check for python-docx footprint
                for fname in z.namelist():
                    content = z.read(fname)
                    if b"python-docx" in content:
                        results["has_python_docx_tag"] = True
                        break

                root_core = ET.fromstring(core_xml)
                ns_core = {"cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties", "dc": "http://purl.org/dc/elements/1.1/"}
                creator_el = root_core.find("dc:creator", ns_core)
                mod_el = root_core.find("cp:lastModifiedBy", ns_core)
                rev_el = root_core.find("cp:revision", ns_core)

                if creator_el is not None:
                    results["creator"] = creator_el.text
                if mod_el is not None:
                    results["last_modified_by"] = mod_el.text
                if rev_el is not None:
                    results["revision"] = rev_el.text

                root_app = ET.fromstring(app_xml)
                tt_el = root_app.find("{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}TotalTime")
                if tt_el is not None and tt_el.text:
                    results["total_time_mins"] = int(tt_el.text)


        except Exception as e:
            results["error"] = str(e)

        return results
