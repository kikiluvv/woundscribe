import typer
from rich.console import Console
from core import ocr, parser, splitter, db
from pathlib import Path

app = typer.Typer()
console = Console()

@app.command()
def process(
    pdf_path: str = typer.Argument(..., help="Path to the monolithic wound note PDF."),
    output: str = typer.Option("./output", "--output", "-o", help="Output folder for processed PDFs."),
):

    console.rule("[bold green]WoundScribe – PDF Processor[/]")
    console.print(f"📄 Processing: {pdf_path}")

    # step 1 – OCR
    page_texts = ocr.extract_texts(pdf_path)
    console.print(f"🧠 OCR complete for {len(page_texts)} pages")

    # step 2 – parse document boundaries
    docs = parser.detect_docs(page_texts)
    console.print(f"📑 Detected {len(docs)} patient sections")

    # step 3 – load DB
    patient_db = db.load_db()

    # step 4 – split + name
    splitter.split_pdf(pdf_path, docs, output, patient_db)

    # step 5 – save updated DB
    db.save_db(patient_db)
    console.rule("[bold green]✅ Finished[/]")

@app.command()
def assign(
    name: str = typer.Argument(..., help="Full name of the patient."),
    clinic: str = typer.Option(..., "--clinic", "-c", help="Clinic name to assign.")
):
    """
    Assign or update a patient’s clinic.
    """
    import datetime
    patient_db = db.load_db()

    patient_db[name] = {
        "clinic": clinic,
        "last_updated": datetime.date.today().isoformat()
    }

    db.save_db(patient_db)
    console.print(f"✅ Assigned [bold]{name}[/] to clinic [cyan]{clinic}[/]")

@app.command()
def list():
    """
    List all known patients and their assigned clinics.
    """
    from rich.table import Table

    patient_db = db.load_db()

    if not patient_db:
        console.print("[yellow]⚠️ No patients found in database yet.[/]")
        return

    table = Table(title="📋 Known Patients", show_lines=True)
    table.add_column("Name", style="bold white")
    table.add_column("Clinic", style="cyan")
    table.add_column("Last Updated", style="dim")

    for name, data in sorted(patient_db.items()):
        clinic = data.get("clinic", "Unknown")
        last_updated = data.get("last_updated", "—")
        table.add_row(name, clinic, last_updated)

    console.print(table)

@app.command()
def remove(
    name: str = typer.Argument(..., help="Full name of the patient to remove.")
):
    """
    Remove a patient from the database.
    """
    patient_db = db.load_db()

    if name not in patient_db:
        console.print(f"[red]❌ {name} not found in database.[/]")
        raise typer.Exit(code=1)

    del patient_db[name]
    db.save_db(patient_db)
    console.print(f"🗑️ Removed [bold]{name}[/] from database.")

@app.command()
def rename(
    old_name: str = typer.Argument(..., help="Current name in the database."),
    new_name: str = typer.Argument(..., help="New name to assign.")
):
    """
    Rename a patient in the database.
    """
    import datetime
    patient_db = db.load_db()

    if old_name not in patient_db:
        console.print(f"[red]❌ {old_name} not found in database.[/]")
        raise typer.Exit(code=1)

    data = patient_db.pop(old_name)
    data["last_updated"] = datetime.date.today().isoformat()
    patient_db[new_name] = data

    db.save_db(patient_db)
    console.print(f"✏️ Renamed [bold]{old_name}[/] → [green]{new_name}[/]")


if __name__ == "__main__":
    app()
