import uvicorn
from fastapi import FastAPI, Request, HTTPException
from starlette.responses import JSONResponse

from src.analyse import analyse_from_xml_structure

app = FastAPI()


@app.get("/process_metadata")
async def process_metadata(request: Request):
    # Accessing query string parameters from the Request object
    xml_url = request.query_params.get("xml")
    threshold = request.query_params.get("threshold")

    try:
        data = analyse_from_xml_structure(xml_url, threshold)
        # Set custom headers in the response
        headers = {
            "Access-Control-Allow-Origin": "*",  # This allows all origins. Adjust this value to restrict allowed origins.
        }
        return JSONResponse(content=data, headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000)
