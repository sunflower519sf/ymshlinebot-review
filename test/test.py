from datetime import datetime, timedelta
import time
import re

newtoday1 = datetime.utcnow() + timedelta(hours=8)
time.sleep(3)
newtoday2 = datetime.utcnow() + timedelta(hours=8)
print(newtoday1, newtoday2)
# print(re.findall(r'\d+', newtoday.strftime('%Y-%m-%d %H:%M:%S')))
a = newtoday1.strftime('%Y-%m-%d %H:%M:%S')
b = newtoday2.strftime('%Y-%m-%d %H:%M:%S')
print(a, b)
if a > b:
    print(True)
elif a < b:
    print(False)
else:
    print("no")