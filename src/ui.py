import PySimpleGUI as sg


def getConfigFromUser():
    layout = [
        [sg.Text("API ID", size=(15, 1)), sg.InputText(size=(42, 1))],
        [sg.Text("API Hash", size=(15, 1)), sg.InputText(size=(42, 1))],
        [sg.Text("Phone", size=(15, 1)), sg.InputText("+xxxxxxxxxxx", size=(42, 1))],
        [sg.Submit("Save"), sg.Cancel()],
    ]
    window = sg.Window("Setup", layout, element_justification="c")
    event, values = window.read()
    window.close()
    if event == "Cancel":
        exit()
    return values[0], values[1], values[2]


def getPass():
    layout = [
        [
            sg.Text("Password", size=(15, 1)),
            sg.InputText("", key="Password", password_char="*"),
        ],
        [sg.Submit("OK"), sg.Cancel()],
    ]
    window = sg.Window("Password", layout, element_justification="c")
    event, values = window.read()
    window.close()
    if event == "Cancel":
        exit()
    return values["Password"]


def getAuthCode():
    layout = [
        [sg.Text("Code", size=(15, 1)), sg.InputText(size=(42, 1))],
        [sg.Submit("Next"), sg.Cancel()],
    ]
    window = sg.Window("Phone Number Authentication", layout, element_justification="c")
    event, values = window.read()
    window.close()
    if event == "Cancel":
        exit()
    return values[0]


def getChannel(channels: list):
    layout = [
        [sg.Text("Channel Name"), sg.Combo(channels, readonly=True)],
        [sg.Submit("OK"), sg.Cancel()],
    ]
    window = sg.Window(
        "Select Signal Provider Channel", layout, element_justification="c"
    )
    event, values = window.read()
    window.close()
    if event == "Cancel":
        exit()
    return values[0]


import os, signal


def TaskStopper(pid, Driver):
    prm_layout = [[sg.Text("The program is running")], [sg.Cancel()]]
    prm_window = sg.Window(
        "Telegram Trading Bot", size=(350, 70), element_justification="c"
    ).Layout(prm_layout)
    while True:
        event, values = prm_window.Read(timeout=0)
        if event == "Cancel":
            prm_window.close()
            Driver.quit()
            os.kill(pid, signal.SIGINT)
            break
