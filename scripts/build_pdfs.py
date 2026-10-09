"""Genera los tres PDF ficticios que usa el RAG, en data/docs/.

El contenido es original y ficticio, escrito para ser coherente con los equipos y las
magnitudes de la base de datos (codigos P-xxx, M-xxx, C-xxx, V-xxx, T-xxx).

Uso: python scripts/build_pdfs.py
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parents[1] / "data" / "docs"
DISCLAIMER = "Documento ficticio elaborado con fines academicos. No debe usarse en una instalacion real."

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, spaceAfter=10)
BODY = ParagraphStyle("BODY", parent=styles["BodyText"], fontSize=10.5, leading=15, spaceAfter=6)
BULLET = ParagraphStyle("BULLET", parent=BODY, leftIndent=14, bulletIndent=4, spaceAfter=3)
TITLE = ParagraphStyle("TITLE", parent=styles["Title"], fontSize=22, spaceAfter=18)
SUB = ParagraphStyle("SUB", parent=styles["BodyText"], fontSize=11, alignment=1, textColor=colors.grey)


def table(rows, widths):
    t = Table(rows, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF4")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9AA5B1")),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def P(text):
    return Paragraph(text, BODY)


def B(items):
    return [Paragraph(i, BULLET, bulletText="•") for i in items]


def build(filename: str, code: str, title: str, subtitle: str, sections: list[tuple[str, list]]):
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(2 * cm, 1.2 * cm, f"{code} | {DISCLAIMER}")
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Pagina {doc.page}")
        canvas.restoreState()

    story: list = [Spacer(1, 5 * cm), Paragraph(title, TITLE), Paragraph(subtitle, SUB), Spacer(1, 1 * cm),
                   Paragraph(f"Codigo del documento: {code}", SUB), Paragraph("Version 1.0 - Octubre de 2026", SUB),
                   Spacer(1, 1 * cm), Paragraph(DISCLAIMER, SUB)]
    for heading, content in sections:
        story.append(PageBreak())
        story.append(Paragraph(heading, H1))
        story.extend(content)
    doc = SimpleDocTemplate(str(OUT / filename), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm, title=title, author="Planta ficticia")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def manual_mantenimiento():
    sections = [
        ("1. Objetivo y alcance", [
            P("Este manual define las tareas y las frecuencias de mantenimiento preventivo de los equipos "
              "rotativos y electricos de la planta: bombas (codigos P-101 a P-110), motores (M-301 a M-310), "
              "compresores (C-201 a C-208), ventiladores (V-401 a V-406) y transformadores (T-501 a T-506)."),
            P("Las frecuencias indicadas son las de referencia para un equipo en servicio normal. Un equipo de "
              "criticidad alta se inspecciona con la frecuencia indicada o con la mitad del intervalo, lo que "
              "resulte mas exigente. Los equipos de criticidad baja pueden extender el intervalo hasta un 25%, "
              "con aprobacion del supervisor."),
            P("Toda tarea preventiva se registra como una orden de mantenimiento de tipo preventivo, con las horas "
              "trabajadas y los repuestos utilizados."),
        ]),
        ("2. Bombas centrifugas", [
            P("Aplica a P-101 a P-110."),
            table([
                ["Tarea", "Frecuencia"],
                ["Inspeccion visual de fugas en el sello mecanico", "Mensual"],
                ["Lubricacion de rodamientos con grasa NLGI 2", "Cada 3 meses"],
                ["Verificacion de alineacion bomba-motor", "Cada 6 meses"],
                ["Revision del sello mecanico y cambio si hay desgaste", "Anual"],
                ["Limpieza de filtros de succion", "Cada 2 meses"],
            ], [10 * cm, 6 * cm]),
            Spacer(1, 8),
            P("Si se detecta una fuga continua en el sello, la bomba pasa a estado en mantenimiento y se abre "
              "una orden correctiva de prioridad media. La alineacion fuera de tolerancia es la causa mas "
              "frecuente de vibracion elevada en bombas."),
        ]),
        ("3. Motores electricos", [
            P("Aplica a M-301 a M-310."),
            table([
                ["Tarea", "Frecuencia"],
                ["Lubricacion de rodamientos con grasa de base litio", "Cada 2.500 horas de funcionamiento o cada 4 meses, lo que ocurra primero"],
                ["Limpieza de aletas de refrigeracion y rejillas", "Cada 3 meses"],
                ["Medicion de resistencia de aislacion del bobinado", "Anual"],
                ["Revision de bornes y conexiones", "Cada 6 meses"],
                ["Medicion de corriente y comparacion con la placa", "Mensual"],
            ], [8 * cm, 8 * cm]),
            Spacer(1, 8),
            P("Un motor que opera de forma sostenida por encima de su corriente nominal debe revisarse por "
              "sobrecarga mecanica o desbalance de tension antes de volver a su regimen normal."),
        ]),
        ("4. Compresores de tornillo", [
            P("Aplica a C-201 a C-208."),
            table([
                ["Tarea", "Frecuencia"],
                ["Cambio del filtro de aire de admision", "Cada 1.000 horas de funcionamiento"],
                ["Cambio de aceite y del filtro de aceite", "Cada 4.000 horas de funcionamiento"],
                ["Revision del separador de aceite", "Cada 8.000 horas de funcionamiento"],
                ["Prueba de la valvula de seguridad", "Anual"],
                ["Drenaje de condensados del tanque", "Semanal"],
            ], [8 * cm, 8 * cm]),
            Spacer(1, 8),
            P("La presion normal de trabajo de los compresores esta por debajo de 8,5 bar. Una presion sostenida "
              "por encima de ese valor indica una posible falla del control de carga o filtros saturados."),
        ]),
        ("5. Ventiladores y transformadores", [
            P("Ventiladores axiales (V-401 a V-406):"),
            *B(["Balanceo del rotor: una vez por ano o cuando la vibracion supere el umbral de alerta.",
                "Tension y estado de las correas: cada 3 meses.",
                "Limpieza de alabes: cada 6 meses."]),
            P("Transformadores de distribucion (T-501 a T-506):"),
            *B(["Inspeccion termografica de bornes y conexiones: cada 6 meses.",
                "Ajuste de bornes con torque especificado: una vez por ano.",
                "Analisis de aceite dielectrico: una vez por ano.",
                "Verificacion del nivel de aceite y de las silicagel: cada 3 meses."]),
        ]),
    ]
    build("manual_mantenimiento_preventivo.pdf", "MAN-001", "Manual de Mantenimiento Preventivo",
          "Equipos rotativos y electricos de la planta", sections)


def procedimiento_alarmas():
    sections = [
        ("1. Objetivo y niveles de severidad", [
            P("Este procedimiento indica como responder a las alarmas generadas por el sistema de telemetria. "
              "Cada alarma tiene una de dos severidades, segun el umbral que supere el sensor:"),
            table([
                ["Severidad", "Condicion", "Tiempo maximo de respuesta", "Orden asociada"],
                ["Alerta", "El valor supera el umbral de alerta del sensor", "24 horas", "Correctiva de prioridad media"],
                ["Critica", "El valor supera el umbral critico del sensor", "2 horas", "Correctiva de prioridad alta"],
            ], [2.6 * cm, 5.4 * cm, 4 * cm, 4 * cm]),
            Spacer(1, 8),
            P("El tiempo de respuesta se cuenta desde el inicio de la alarma. Una alarma que sigue abierta al "
              "cambio de turno se informa explicitamente al turno entrante."),
        ]),
        ("2. Alarmas de vibracion", [
            P("Los umbrales de referencia son 4,5 mm/s de alerta y 7,1 mm/s critico para bombas, motores y "
              "ventiladores, y 5,6 mm/s de alerta y 9,0 mm/s critico para compresores."),
            P("<b>Alarma de alerta:</b>"),
            *B(["Confirmar la lectura con un segundo instrumento portatil.",
                "Inspeccionar fijaciones, base y acoples.",
                "Programar la verificacion de alineacion y del estado de los rodamientos dentro de las 24 horas."]),
            P("<b>Alarma critica:</b>"),
            *B(["Reducir la carga del equipo de inmediato y avisar al supervisor.",
                "Inspeccionar rodamientos, alineacion, desbalance y aflojamiento mecanico.",
                "Si la vibracion no baja del umbral critico en 30 minutos, detener el equipo mediante el procedimiento de bloqueo y etiquetado.",
                "Abrir una orden correctiva de prioridad alta y asignar un tecnico de especialidad mecanica."]),
            P("En compresores como el C-201, una vibracion critica sostenida obliga ademas a revisar el acople "
              "y el estado del aceite antes de volver a arrancar."),
        ]),
        ("3. Alarmas de temperatura", [
            P("Los umbrales de referencia son 80 a 85 grados C de alerta y 15 grados mas para el critico en "
              "motores, bombas y compresores. Los transformadores tienen 85 grados C de alerta y 105 grados C "
              "critico."),
            P("<b>Alarma de alerta:</b>"),
            *B(["Verificar la ventilacion y que las rejillas esten libres.",
                "Revisar el nivel y el estado de la lubricacion.",
                "Medir la corriente para descartar sobrecarga."]),
            P("<b>Alarma critica:</b>"),
            *B(["Reducir la carga y revisar la causa del calentamiento.",
                "En un motor, si la temperatura no baja en 30 minutos, detenerlo para evitar dano del bobinado.",
                "En un transformador, avisar al supervisor electrico y no volver a cargarlo hasta una inspeccion termografica.",
                "Asignar un tecnico de especialidad lubricacion o electrica segun la causa."]),
        ]),
        ("4. Alarmas de presion y de corriente", [
            P("<b>Presion.</b> Los umbrales son 8,0 bar de alerta y 10,0 bar critico en bombas, y 8,5 bar de "
              "alerta y 10,5 bar critico en compresores."),
            *B(["Alerta: revisar filtros, valvulas y el estado de los sellos.",
                "Critica: aliviar la presion por la valvula de seguridad, detener la fuente de presion y abrir una orden de prioridad alta con un tecnico de instrumentacion."]),
            P("<b>Corriente.</b> El umbral critico es 1,2 veces el umbral de alerta del sensor."),
            *B(["Alerta: comparar con la corriente de placa y revisar la carga mecanica.",
                "Critica: reducir la carga, revisar conexiones y bornes, y abrir una orden de prioridad alta con un tecnico electrico."]),
        ]),
        ("5. Cierre de la alarma", [
            P("Una alarma se considera cerrada cuando el valor del sensor vuelve por debajo del umbral de "
              "alerta y se mantiene asi durante al menos dos lecturas consecutivas."),
            *B(["Registrar en la orden la causa encontrada y la accion realizada.",
                "Si la causa no se identifico, mantener la orden en curso y programar una nueva revision en 7 dias.",
                "Si la misma alarma se repite tres veces en un mes sobre el mismo equipo, escalar al ingeniero de mantenimiento para un analisis de causa raiz."]),
        ]),
    ]
    build("procedimiento_respuesta_alarmas.pdf", "PRO-002", "Procedimiento de Respuesta a Alarmas",
          "Sistema de telemetria de la planta", sections)


def politica_ordenes():
    sections = [
        ("1. Prioridades y plazos de atencion", [
            P("Toda orden de mantenimiento tiene una prioridad que define el plazo maximo para iniciar el trabajo."),
            table([
                ["Prioridad", "Cuando se usa", "Plazo para iniciar el trabajo"],
                ["Alta", "Alarma critica, equipo de criticidad alta detenido o riesgo para las personas", "4 horas"],
                ["Media", "Alarma de alerta o falla que no detiene el proceso", "3 dias"],
                ["Baja", "Mejoras y tareas sin impacto en la operacion", "15 dias"],
            ], [2.6 * cm, 9 * cm, 4.4 * cm]),
            Spacer(1, 8),
            P("Las ordenes preventivas toman la prioridad media, salvo en equipos de criticidad baja, que usan "
              "prioridad baja."),
        ]),
        ("2. Asignacion de tecnicos", [
            P("La asignacion considera la especialidad del tecnico y la causa de la orden:"),
            *B(["Vibracion: especialidad mecanica.",
                "Temperatura: especialidad lubricacion o mecanica.",
                "Presion: especialidad instrumentacion.",
                "Corriente: especialidad electrica."]),
            P("Las ordenes de prioridad alta se asignan al tecnico disponible del turno en curso, aunque su "
              "especialidad no coincida, y se acompanan de un segundo tecnico de la especialidad correcta apenas "
              "este disponible."),
        ]),
        ("3. Bloqueo y etiquetado antes de intervenir", [
            P("Ningun equipo se interviene sin aplicar el procedimiento de bloqueo y etiquetado. Los pasos son:"),
            *B(["Avisar al operador del area y al supervisor.",
                "Detener el equipo por su parada normal.",
                "Aislar todas las fuentes de energia electrica, neumatica e hidraulica.",
                "Colocar el candado personal y la etiqueta con nombre y fecha.",
                "Liberar la energia residual y verificar la ausencia de energia antes de comenzar.",
                "Al terminar, retirar solo el candado propio y avisar al operador antes de reenergizar."]),
            P("Los elementos de proteccion personal minimos son casco, anteojos de seguridad, guantes y calzado "
              "de seguridad. Para trabajos en transformadores se agregan guantes dielectricos y proteccion facial."),
        ]),
        ("4. Cierre de una orden", [
            P("Una orden solo puede pasar a estado cerrada cuando incluye:"),
            *B(["La descripcion del trabajo realizado y la causa encontrada.",
                "Las horas trabajadas.",
                "Los repuestos utilizados, si los hubo.",
                "La confirmacion del operador de que el equipo funciona con normalidad."]),
            P("Las ordenes correctivas originadas por una alarma se cierran solo despues de que la alarma haya "
              "terminado. Las ordenes que superan el plazo de su prioridad sin iniciarse se informan en la "
              "reunion semanal de mantenimiento."),
        ]),
    ]
    build("politica_gestion_ordenes.pdf", "POL-003", "Politica de Gestion de Ordenes de Mantenimiento",
          "Prioridades, asignacion, seguridad y cierre", sections)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manual_mantenimiento()
    procedimiento_alarmas()
    politica_ordenes()
    for p in sorted(OUT.glob("*.pdf")):
        print(p.name, p.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
