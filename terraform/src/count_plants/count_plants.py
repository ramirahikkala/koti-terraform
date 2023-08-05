import json
import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]

CREDS = json.loads(os.environ.get("KASVISLUETTELO_CREDS"))
# The ID of a sample document.
DOCUMENT_ID = CREDS["document_id"]


def lambda_handler(event, context):
    """Shows basic usage of the Docs API.
    Returns the title of a sample document and plant counts under each heading.
    """
    creds = service_account.Credentials.from_service_account_info(CREDS, scopes=SCOPES)

    try:
        service = build("docs", "v1", credentials=creds)

        # Retrieve the documents contents from the Docs service.
        document = service.documents().get(documentId=DOCUMENT_ID).execute()

        # Get the plants under each heading in the document
        plants_under_headings = get_plants(document)
        body = {"title": document.get("title"), "plantCounts": []}
        total_plants = 0  # Variable to store total plants count
        for heading, subheadings in plants_under_headings.items():
            heading_total_plants = sum(len(plants) for plants in subheadings.values())
            total_plants += heading_total_plants  # Adding to the total plants count
            heading_info = {
                "heading": heading,
                "totalPlants": heading_total_plants,
                "subheadings": [],
            }
            for subheading, plants in subheadings.items():
                subheading_info = {"subheading": subheading, "plants": len(plants)}
                heading_info["subheadings"].append(subheading_info)
            body["plantCounts"].append(heading_info)
        
        body['totalPlants'] = total_plants  # Adding total count to the body

        response = {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Origin": "*",  #'https://temperature-visualizer.vercel.app',
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
            },
            "body": json.dumps(body),
        }

        return response
    except HttpError as err:
        return {
            "isBase64Encoded": False,
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Origin": "*",  #'https://temperature-visualizer.vercel.app',
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
            },
            "body": json.dumps({"error": str(err)}),
        }


def get_plants(document):
    """Gets and returns a dictionary where keys are the headings and values are lists of plants under each heading."""
    main_heading = ""
    sub_heading = ""
    plants_under_headings = {}
    for element in document.get("body").get("content"):
        if "paragraph" in element:
            paragraph = element.get("paragraph")
            if "namedStyleType" in paragraph.get("paragraphStyle"):
                for text_element in element.get("paragraph").get("elements"):
                    text_run = text_element.get("textRun")
                    if text_run and "content" in text_run:
                        if (
                            paragraph.get("paragraphStyle").get("namedStyleType")
                            == "HEADING_1"
                        ):
                            main_heading = text_run.get("content").strip()
                            if main_heading not in plants_under_headings:
                                plants_under_headings[main_heading] = {}
                            sub_heading = (
                                ""  # Reset sub_heading for each new main_heading
                            )
                        elif (
                            paragraph.get("paragraphStyle").get("namedStyleType")
                            == "HEADING_2"
                        ):
                            sub_heading = text_run.get("content").strip()
                            if sub_heading not in plants_under_headings[main_heading]:
                                plants_under_headings[main_heading][sub_heading] = []
                        elif main_heading:
                            if sub_heading:
                                plants_under_headings[main_heading][sub_heading].append(
                                    text_run.get("content").strip()
                                )
                            else:
                                if "Other" not in plants_under_headings[main_heading]:
                                    plants_under_headings[main_heading]["Other"] = []
                                plants_under_headings[main_heading]["Other"].append(
                                    text_run.get("content").strip()
                                )
    return plants_under_headings


if __name__ == "__main__":
    print(lambda_handler(None, None))
