content_string = "Student files: "
data = {"test1": "1", "test2": "2", "test3": "3", "test4": "4"}

for key in data.items():
    add = f"\n{key}: "
    content_string += add

print(content_string)