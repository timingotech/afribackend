import pathlib,sys
p=pathlib.Path('logs/email_send.log')
if not p.exists():
    print('no log')
    sys.exit(0)
for line in p.read_text().splitlines():
    if 'adebolaaaaa' in line or 'oyenugaridwan' in line:
        print(line)
