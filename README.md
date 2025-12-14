## COMPILATION

to install dependencies:
```
pip install -r requirements.txt
```

To build the application:
```
pyinstaller --noconfirm --onefile --windowed --uac-admin --collect-all customtkinter --name "ContextManager" main.py
```

To run the application:
```
ContextManager.exe
```

## RUNNING FROM RELEASE
obs: ensure to have admin permissions and customtkinter installed

To install customtkinter: ** ESSENCIAL **
```
pip install customtkinter
```

To run the application:
```
ContextManager.exe
```

## RUNNING FROM SOURCE

To run the application:
```
python main.py
```

## RUNNING FROM VENV

To run the application:
```
.venv\Scripts\python.exe main.py
```