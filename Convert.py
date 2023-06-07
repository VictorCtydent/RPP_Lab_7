import uvicorn
import psycopg2 as pg
from fastapi import FastAPI, HTTPException
import re

app = FastAPI()

conn = pg.connect(user='postgres', password='postgres', host='localhost', port='5432', database='Lab7')
cursor = conn.cursor()


def get_conversion_rate(base_currency, converted_currency):
    cursor.execute("""SELECT crv.rate FROM currency_rates_values crv
                      JOIN currency_rates cr ON crv.currency_rate_id = cr.id
                      WHERE cr.base_currency = %s AND crv.currency_code = %s""", (base_currency, converted_currency,))
    result = cursor.fetchone()
    if result:
        return result[0]
    return None


@app.get("/convert")
def convert_get(baseCurrency: str, convertedCurrency: str, sum: float):
    try:
        conversion_rate = get_conversion_rate(baseCurrency, convertedCurrency)
        if conversion_rate is None:
            raise HTTPException(status_code=500, detail="Invalid conversion rate")

        converted_sum = float(sum) * float(conversion_rate)
        return {'converted': converted_sum}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    uvicorn.run(app, port=10607, host='localhost')
