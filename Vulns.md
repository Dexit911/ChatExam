### Authentication
- No auth check for create_exam api, anyone can create an exam.
- Creates the exam for the sessions teacher_id but if this session is null it will still create it AND for EVERY TEACHER.

# I think I solved most of the functions used in routes - Dex



### Information Disclosure
- Leaking seb config files for all exams. Can see ANYONES EXAMS just by changing /seb-config/4.seb .
- This leaks the session cookie of all students making people able to login as them.
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "https://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
          <key>startURL</key>
          <string>http://192.168.0.221/student/exam/04f35a?token=eyJzdHVkZW50X2lkIjozfQ.aO9cpg.JIjE06VzCzOUav7M25LFmlJO2WE</string>

- This also allows anyone to see any exam beforehand by changing their user agent to be SafeExamBrowser as seen in security.py.
- Thus this is a chained attack.

# Still in progress...


### GitHub link vulnerable

- Able to put whatever as link so chatgpt etc work.
- But also able to put localhost:80/ which can lead to csrf, example i put link to localhost/api/get_exams and boom ez.

# I validate link with recompile. Try to mess it up... I dare you - Dex

# provided by yours truly - alanoo 