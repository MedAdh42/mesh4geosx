from pathlib import Path

# Create a Path object for a file
file_path = Path("/path/to/file.txt")

# Check if the file exists
if file_path.exists():
    print("File exists.")
else:
    print("File does not exist.")

# Get the file name
file_name = file_path.name
print("File name:", file_name)

# Get the file extension
file_extension = file_path.suffix
print("File extension:", file_extension)

# Get the parent directory
parent_directory = file_path.parent
print("Parent directory:", parent_directory)

# Create a new directory
new_directory = Path("/path/to/new_directory")
new_directory.mkdir(parents=True, exist_ok=True)
print("New directory created.")

# List all files in a directory
directory_path = Path("/path/to/directory")
for file in directory_path.iterdir():
    if file.is_file():
        print(file.name)

# Check if a path is a file or directory
path = Path("/path/to/some_path")
if path.is_file():
    print("It is a file.")
elif path.is_dir():
    print("It is a directory.")
else:
    print("It is neither a file nor a directory.")
