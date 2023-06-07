import uvicorn
import psycopg2 as pg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.responses import JSONResponse
import re
from typing import List

app = FastAPI()

conn = pg.connect(user='postgres', password='postgres', host='localhost', database='Lab7')
cursor = conn.cursor()


class Converted(BaseModel):
    code: str
    rate: float


class RequestBody(BaseModel):
    baseCurrency: str
    rates: List[Converted]


def check(name):
    cursor.execute("""SELECT id FROM currency_rates 
                      WHERE base_currency = %s""", (name,))
    data_id = cursor.fetchall()
    data_id = re.sub(r"[^0-9]", r"", str(data_id))
    return data_id


@app.post("/load")
async def load_payload(request: RequestBody):
    base_currency = request.baseCurrency
    rates = request.rates

    try:
        cursor.execute("SELECT id FROM currency_rates WHERE base_currency = %s", (base_currency,))
        data_id = cursor.fetchone()
        if not data_id:
            cursor.execute("INSERT INTO currency_rates (base_currency) VALUES (%s)", (base_currency,))
            conn.commit()
            cursor.execute("SELECT id FROM currency_rates WHERE base_currency = %s", (base_currency,))
            data_id = cursor.fetchone()

        for rate in rates:
            cursor.execute(
                "INSERT INTO currency_rates_values (currency_code, rate, currency_rate_id) VALUES (%s, %s, %s)",
                (rate.code, rate.rate, data_id[0]))
            conn.commit()

        return JSONResponse(content={"message": "Success"}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    uvicorn.run(app, port=10670, host='localhost')
