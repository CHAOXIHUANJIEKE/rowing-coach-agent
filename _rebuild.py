# AI生成
import zipfile, os

src = r'D:\果办\OfficeAce\workspace\20261010135443\rowing-coach-agent'
zip_path = r'D:\Desktop\本科生组-U157-智科队-王琦.zip'
exclude_dirs = {'__pycache__'}

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            full = os.path.join(root, f)
            arc = os.path.relpath(full, os.path.dirname(src))
            zf.write(full, arc)

print(f'ZIP: {os.path.getsize(zip_path)/1024/1024:.2f} MB, {len(zipfile.ZipFile(zip_path).namelist())} files')
# 验证 .env.example 在内
names = zipfile.ZipFile(zip_path).namelist()
print('.env.example in ZIP:', any('.env.example' in n for n in names))