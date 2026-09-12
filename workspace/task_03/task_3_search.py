# Lab Task: Sorting and Binary Search
# Student: Bheesham Kumar Sajnani (25F-DS-020)

def binary_search(arr, target):
    low = 0
    high = len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1

numbers = [14, 28, 33, 42, 55, 68, 77, 89, 95]
target = 55
print(f'[+] Sorted Array: {numbers}')
print(f'[+] Searching for target: {target}')
idx = binary_search(numbers, target)
if idx != -1:
    print(f'[+] Success: Found {target} at index {idx}')
else:
    print(f'[-] Element {target} not found in array')
