# AstraSec AI · Entrega a IBM SkillsBuild

AstraSec AI organiza evidencias criptográficas de un entorno autorizado y conserva un expediente revisable con fuentes, decisiones e informes.

Esta copia pública incluye el prototipo, un recorrido guiado y datos ficticios. Los identificadores de configuración y del resultado archivado fueron sustituidos para la publicación. Los datos del laboratorio y las capturas de pantalla se conservan en la documentación privada del equipo.

## Ejecutar la demostración

Con Python 3.14, crea un entorno virtual e instala las dependencias. Ejemplo para PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:AI_PROVIDER = "demo"
.\.venv\Scripts\python.exe -m streamlit run app/main.py --server.address 127.0.0.1
```

- **Demo de un caso** presenta los seis pasos de la revisión, desde la verificación de la captura hasta la recuperación del informe.
- **Agente → Prueba real IBM · datos ficticios** muestra el resultado archivado de IBM watsonx Orchestrate. La demostración no requiere credenciales.
- **Reportes** permite recuperar los expedientes creados en la ejecución local.
- Las pruebas se ejecutan con `python -m pytest -q` en modo demo.

IBM Bob apoyó el desarrollo inicial. IBM watsonx Orchestrate produjo un plan sobre fuentes autorizadas. Las verificaciones de integridad y el guardado se ejecutan localmente y la revisión queda a cargo de una persona.

## Experimento complementario en IBM Quantum

En `ibm_fez`, con 1,024 mediciones por par, los bits coincidieron en el 95.51 % de los resultados del par Bell y en el 50.10 % del control independiente. Es una comparación de correlaciones en la base medida. No certifica entrelazamiento ni seguridad poscuántica.
