

# Java API Demo – Hola Mundo (JDK 17 + VS Code)

Guía paso a paso para crear una API básica de **Hola Mundo** en Java usando **JDK 17 (Eclipse Temurin)**, **Visual Studio Code** y **PowerShell**, utilizando **rutas relativas**.

---

## 1. Instalar JDK 17 (Eclipse Temurin)

1. Accede a la página oficial de descargas:
   [https://adoptium.net/es/temurin/releases?version=17](https://adoptium.net/es/temurin/releases?version=17)

2. Descarga:

   * **JDK**
   * **Windows x64**
   * Instalador **.msi**

3. Ejecuta el instalador y asegúrate de:

   * Marcar **Add to PATH**
   * Configurar **JAVA_HOME**

4. Finaliza la instalación.

5. **Reinicia el equipo**.

---

## 2. Validar instalación de Java

Abre **PowerShell** y ejecuta:

```powershell
java --version
javac --version
```

Salida esperada (ejemplo):

```text
openjdk version "17.x"
```

Si no aparece la versión, revisa las variables de entorno y vuelve a reiniciar.

---

## 3. Instalar Visual Studio Code

1. Instala **Visual Studio Code**.
2. Abre VS Code.
3. Instala la extensión:

   * **Extension Pack for Java**

Esto habilita soporte completo para desarrollo Java.

---

## 4. Crear el proyecto (rutas relativas)

Desde **PowerShell**, ubícate en tu carpeta de trabajo:

```powershell
cd Documents
```

Crea el proyecto:

```powershell
mkdir java-api-demo
cd java-api-demo
```

---

## 5. Estructura del proyecto

```powershell
mkdir src\main\java\app
```

Estructura final:

```text
java-api-demo
└── src
    └── main
        └── java
            └── app
```

---

## 6. Crear aplicación Hola Mundo

Crea el archivo:

```powershell
notepad src\main\java\app\HelloWorld.java
```

Contenido:

```java
package app;

public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hola Mundo desde Java API demo!");
    }
}
```

---

## 7. Compilar y ejecutar

Desde la raíz del proyecto:

```powershell
javac src\main\java\app\HelloWorld.java -d out
java -cp out app.HelloWorld
```

Salida esperada:

```text
Hola Mundo desde Java API demo!
```

---

## 8. API HTTP básica (sin frameworks)

Reemplaza el contenido de `HelloWorld.java`:

```java
package app;

import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;

public class HelloWorld {

    public static void main(String[] args) throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(8000), 0);
        server.createContext("/hola", new HolaHandler());
        server.start();

        System.out.println("Servidor activo en http://localhost:8000/hola");
    }

    static class HolaHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            String response = "Hola Mundo desde API!";
            exchange.sendResponseHeaders(200, response.getBytes().length);

            try (OutputStream os = exchange.getResponseBody()) {
                os.write(response.getBytes());
            }
        }
    }
}
```

Compila y ejecuta:

```powershell
javac src\main\java\app\HelloWorld.java -d out
java -cp out app.HelloWorld
```

Abre en el navegador:

```text
http://localhost:8000/hola
```

---

## 9. Abrir el proyecto en VS Code

```powershell
code .
```

VS Code detectará automáticamente el proyecto Java y permitirá ejecutar y depurar desde el editor.

---

## 10. Notas finales

* Se usan **rutas relativas** para evitar dependencias del sistema.
* Esta estructura es compatible con una futura migración a **Maven** o **Spring Boot**.
* Ideal para pruebas rápidas o demos técnicas.

---

### Próximos pasos recomendados

* Convertir el proyecto a **Maven**
* Crear una API REST con **Spring Boot**
* Agregar tests y empaquetado

Indica el siguiente paso y continúo.
