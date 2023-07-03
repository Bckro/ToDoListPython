import PySimpleGUI as gui
import sys
import sqlite3

class User:
    def __init__(self, id, name, login, password):
        self.Id = id
        self.Name = name
        self.Login = login
        self.Password = password

class UserManager:
    def __init__(self, conn):
        self.conn = conn
        self.currentUser = User(1, "", "", "")

    def CreateUser(self, name, login, password):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO Users (Name, Login, Password) VALUES (?, ?, ?)", (name, login, password))
        self.conn.commit()

    def IsLoginTaken(self, login):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE Login = ?", (login,))
        return cursor.fetchone() is not None

    def GetUser(self, login, password):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE Login = ? AND Password = ?", (login, password))
        user = cursor.fetchone()
        if user:
            return User(*user)
        return None

    def UserExists(self, login, password):
        user = self.GetUser(login, password)
        if user:
            self.currentUser = user
            return True
        return False

class TODOTask:
    def __init__(self, id, title, desc, done, userId):
        self.Id = id
        self.Title = title
        self.Desc = desc
        self.Done = done
        self.UserID = userId

class TODOTaskManager:
    def __init__(self, conn):
        self.conn = conn
        self.userTasks = {}
        self.currentUser = None

    def GetUserTasks(self, userId):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM Tasks WHERE UserId = ?", (userId,))
        tasks = cursor.fetchall()
        return [TODOTask(*task) for task in tasks]

    def GetUserTitles(self, tasks):
        return [task.Title for task in tasks]

    def UpdateListsAndCombo(self, task, window, userId):
        if userId not in self.userTasks:
            self.userTasks[userId] = []

        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO Tasks (Title, Description, Done, UserId) VALUES (?, ?, ?, ?)",
                       (task.Title, task.Desc, task.Done, task.UserID))
        self.conn.commit()

        self.userTasks[userId].append(task)
        window["titles"].update(values=self.GetUserTitles(self.userTasks[userId]), value=task.Title)
        self.ShowTask(task.Title, window, userId)

    def ClearInputs(self, window):
        window["input_title"].update("")
        window["input_desc"].update("")

    def ShowTask(self, title, window, userId):
        task = next((t for t in self.userTasks[userId] if t.Title == title), None)
        if task:
            window["id"].update(task.Id)
            window["title"].update(task.Title)
            window["desc"].update(task.Desc)
            window["done"].update(task.Done)

    def ToggleFinished(self, title, userId):
        task = next((t for t in self.userTasks[userId] if t.Title == title), None)
        if task:
            task.Done = not task.Done

            cursor = self.conn.cursor()
            cursor.execute("UPDATE Tasks SET Done = ? WHERE Title = ?", (task.Done, title))
            self.conn.commit()

    def RemoveTask(self, title, window, userId):
        task = next((t for t in self.userTasks[userId] if t.Title == title), None)
        if task:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM Tasks WHERE Title = ?", (title,))
            self.conn.commit()

            self.userTasks[userId].remove(task)
            window["titles"].update(values=self.GetUserTitles(self.userTasks[userId]), value="")

conn = sqlite3.connect('database.db')
userManager = UserManager(conn)
taskManager = TODOTaskManager(conn)

def mainWindow():
    taskNo = 1
    userId = userManager.currentUser.Id
    userTasks = taskManager.GetUserTasks(userId)
    taskManager.userTasks[userId] = userTasks
    titles = taskManager.GetUserTitles(userTasks)

    UI = [
        [gui.Text(f"Logged in as {userManager.currentUser.Name}", size=(44, 1), font=("Cambria", 14)),
        gui.Button("Logout", size=(10, 1), font=("Cambria", 12)),
        gui.Button("Exit", size=(10, 1), font=("Cambria", 12))]
    ]

    inputs_layout = [
        [gui.Text("Add Task", font=("Cambria", 16))],
        [gui.Text("Title: "), gui.Input(key="input_title", size=(43, 1))],
        [gui.Multiline(key="input_desc", size=(50, 4))]
    ]

    inputs_layout += [[
        gui.Button("Add", size=(15, 1), font=("Cambria", 12)),
        gui.Button("Remove", button_color="pink", size=(15, 1), font=("Cambria", 12))
        ]]

    output_layout = [
        [gui.Text("Task List", font=("Cambria", 16))],
        [gui.Combo(titles, key="titles", size=(50, 1), enable_events=True)]
    ]

    header = [ 
        [
            gui.Text("Id", size=(5, 1), pad=(0, 0), justification="left"),
            gui.Text("Title", size=(15, 1), pad=(0, 0), justification="left"),
            gui.Text("Description", size=(25, 1), pad=(0, 0), justification="left"),
            gui.Text("Done", size=(4, 1), pad=(0, 0), justification="left")
        ]
    ]

    table = [
        [
            gui.Input(key="id", size=(3, 1), pad=(0, 0)), 
            gui.Input(key="title", size=(15, 1), pad=(0, 0)), 
            gui.Input(key="desc", size=(25, 1), pad=(0, 0)),
            gui.CBox("", key="done", size=(4, 1), enable_events=True)
        ]
    ]

    output_layout += header + table

    layout = UI + inputs_layout + output_layout

    window = gui.Window("TODOList", layout, element_justification="center", font=("Cambria", 12), no_titlebar=True)

    while True:
        event, values = window.read()
        if event == "Logout":
            window.close()
            loginWindow()

        if event == "Exit" or event == gui.WINDOW_CLOSED:
            sys.exit()

        if event == "Add":
            task = TODOTask(taskNo, values["input_title"], values["input_desc"], False, userId)
            taskNo += 1
            taskManager.UpdateListsAndCombo(task, window, userId)
            taskManager.ClearInputs(window)
        
        if event == "titles":
            taskManager.ShowTask(values["titles"], window, userId)

        if event == "done":
            taskManager.ToggleFinished(values["titles"], userId)

        if event == "Remove":
            taskManager.RemoveTask(values["titles"], window, userId)

def loginWindow():
    login_layout = [
        [gui.Text("Login", font=("Cambria", 16))],
        [gui.Text("Login:"), gui.In(key="login", size=(15, 1))],
        [gui.Text("Password:"), gui.In(key="password", size=(15, 1), password_char="•")],     
        [gui.Button("Log In", font=("Cambria", 12))], 
        [gui.Button("Create Account", font=("Cambria", 12))],
        [gui.Button("Exit", size=(10, 1), font=("Cambria", 12))]
    ]
  
    window = gui.Window("Login",
                        login_layout,
                        element_justification="center",
                        font=("Cambria", 12),
                        element_padding=(5, 5),
                        no_titlebar=True)

    while True:
        event, values = window.read()
        if event == "Log In":
            login = values["login"]
            password = values["password"]
            if userManager.UserExists(login, password):
                window.close()
                mainWindow()
            else:
                gui.popup_error("Invalid login or password. Please try again.")

        if event == "Create Account":
            window.close()
            registerWindow()

        if event == "Exit" or event == gui.WINDOW_CLOSED:
            sys.exit()

def registerWindow():
    register_layout = [
        [gui.Text("Create Account", font=("Cambria", 16))],
        [gui.Text("Name:"), gui.In(key="name", size=(15, 1))],
        [gui.Text("Login:"), gui.In(key="login", size=(15, 1))],
        [gui.Text("Password:"), gui.In(key="password", size=(15, 1), password_char="•")],
        [gui.Button("Create", font=("Cambria", 12))],
        [gui.Button("Exit", size=(10, 1), font=("Cambria", 12))]
    ]
  
    window = gui.Window("Register",
                        register_layout,
                        element_justification="center",
                        font=("Cambria", 12),
                        element_padding=(5, 5),
                        no_titlebar=True)

    while True:
        event, values = window.read()
        if event == "Create":
            name = values["name"]
            login = values["login"]
            password = values["password"]
            if userManager.IsLoginTaken(login):
                gui.popup_error("Login is already taken. Please choose a different one.")
            else:
                userManager.CreateUser(name, login, password)
                gui.popup("Account created successfully!")
                window.close()
                loginWindow()

        if event == "Exit" or event == gui.WINDOW_CLOSED:
            sys.exit()

loginWindow()
