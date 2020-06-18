import csv
import requests

""" Constants to access data on Google Sheets. """
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/"
NOTATIONS_SHEET = "1b75J-QTGrujSgF9r0_JPOKkcXAwzFVwpETOAyVBw8ak/"
EXPORT_AS_CSV = "export?format=csv&id=1b75J-QTGrujSgF9r0_JPOKkcXAwzFVwpETOAyVBw8ak&gid=0"
URL = GOOGLE_SHEETS_URL + "d/" + NOTATIONS_SHEET + EXPORT_AS_CSV

""" Returns "Notations" sheets as a csv.reader. """
def data() -> csv.reader:
    with requests.Session() as session:
        return csv.reader(session.get(URL).content.decode("utf-8").splitlines(), delimiter=",")


