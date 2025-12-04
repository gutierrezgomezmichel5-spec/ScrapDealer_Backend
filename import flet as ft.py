import flet as ft
import requests

def main(page: ft.Page):
    page.title = "Login Reciclaje"
    page.window_width = 400
    page.window_height = 500
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"

    usuario = ft.TextField(label="Usuario")
    password = ft.TextField(label="Contraseña", password=True)
    mensaje = ft.Text("")

    def procesar_login(e):
        r = requests.post(
            "http://127.0.0.1:5000/login",
            json={
                "usuario": usuario.value,
                "password": password.value
            }
        )
        data = r.json()
        mensaje.value = data["mensaje"]
        page.update()

    page.add(
        ft.Column(
            width=300,
            controls=[
                ft.Text("Iniciar Sesión", size=24, weight="bold"),
                usuario,
                password,
                ft.ElevatedButton("Entrar", on_click=procesar_login),
                mensaje
            ]
        )
    )

ft.app(target=main)