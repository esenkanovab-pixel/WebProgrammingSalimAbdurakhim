MiniLMS
=======

Локальный запуск проекта (Windows PowerShell):

1. Создать виртуальное окружение и активировать его:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Установить зависимости:

```powershell
pip install -r requirements.txt
```

3. Применить миграции и запустить сервер:

```powershell
venv\Scripts\python.exe manage.py migrate
venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

После запуска откройте http://127.0.0.1:8000 в браузере.

Если у вас уже есть виртуальное окружение, замените команды на ваш путь к `python`.
