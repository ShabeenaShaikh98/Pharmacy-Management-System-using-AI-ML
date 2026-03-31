from pathlib import Path
replacements = {
    'from pharmacy_app.': 'from pharma_django.pharmacy_app.',
    'from ml_engine.': 'from pharma_django.ml_engine.',
    'import pharmacy_app': 'import pharma_django.pharmacy_app',
    'import ml_engine': 'import pharma_django.ml_engine',
}
root = Path('pharma_django')
for file_path in root.rglob('*.py'):
    text = file_path.read_text(encoding='utf-8')
    new_text = text
    for old, new in replacements.items():
        new_text = new_text.replace(old, new)
    if new_text != text:
        file_path.write_text(new_text, encoding='utf-8')
        print(f'patched {file_path}')
