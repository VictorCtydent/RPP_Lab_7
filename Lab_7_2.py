import re

import psycopg2 as pg
import uvicorn
from fastapi import FastAPI, HTTPException

app= FastAPI()

conn = pg.connect(user='postgres', password='postgres', host='localhost', port='5432', database='RPP_7')
cursor=conn.cursor()

def check(name):
    cursor.execute("""select id from currency_rates 
                            where base_currency = %s""", (name,))
    data_id=cursor.fetchall()
    data_id = re.sub(r"[^0-9]", r"", str(data_id))
    print(data_id)
    return (data_id)

def get(name,id):
    print(id,name)
    cursor.execute("""select rate from currency_rates_values 
                              where  currency_rate_id = %s and currency_code =%s""", (id,name,))
    data_id = cursor.fetchall()
    data_id = re.sub(r"[^0-9]", r"", str(data_id))


    return (data_id)


@app.get("/convert")
def convert_get(baseCurrency: str, convertedCurrency: str, sum: float):
    try:
        print(baseCurrency,convertedCurrency,sum)
        baseCurrency=int(check(baseCurrency))
        convertedCurrency=int(get(convertedCurrency,baseCurrency))
        if convertedCurrency != 0 and baseCurrency !=0:
            res=convertedCurrency*sum
            return ({'converted': res})
            raise HTTPException(200)


    except:
        raise HTTPException(500)


if __name__ == '__main__':
    uvicorn.run(app, port=10607, host='localhost')