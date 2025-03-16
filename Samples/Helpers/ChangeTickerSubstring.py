import os
import pandas as pd
import asyncio

"""
This script helps you change the symbol names in your csv files.
BACKUP YOUR DATA BEFORE RUNNING THIS SCRIPT
The purpose is this. CCXTs unified API expects symbols sent in fetch_ohlcv() in the format BTC/USDT
Each market pair can appear in more than 1 exchange and to handle this, users may have store their pairs in
any variety of formats, e.g BTC/USDTbinance,BTCUSDTbinance, BTC/USDT.binance and so on.

'/' does not always seem to come through the json to the plug-in, but, '-' does.

Therefore, for uniformity, rename your tickers in your new database as  BASE-QUOTE.exchange, then in the RTD plugin clients, 
"-" is replaced with "/" when making exchaneg calls, but is left as it is when comunicating with the plugin and amibroker. 
"""


async def change_ticker_substring_by_file_conts(historic_data_dir, file_substring, prior_substring, new_substring):
    files = (os.listdir(historic_data_dir))
    for file in files:
        try:
            if not file_substring in file:
                print(f"Skipping {file}")
                continue
            full_path = os.path.join(historic_data_dir, file)
            if not os.path.isfile(full_path):
                continue
            df_ticker = pd.read_csv(full_path, header=None)
            df_ticker[0] = df_ticker[0].astype(str)
            df_ticker[0] = df_ticker[0].str.replace(prior_substring, new_substring)
            print(f"Changed substring in {file} from {prior_substring} to {new_substring}. Ticker: {df_ticker[0][0]}")
            df_ticker.to_csv(full_path, header=False, index=False, mode="w")

        except Exception as e:
            print(f"Unable to change {file}: ", e)
async def main():
    historic_data_dir = r'path\to\data\directory' #past path to drive container
    # Modify the 3rd and 4th arguments in the tasks below and delete reduant tasks for your own needs.

    task1 = asyncio.create_task( change_ticker_substring_by_file_conts(historic_data_dir,"USDT.csv","/USDTbinance", "-USDT.binance"  ))
    task2 = asyncio.create_task( change_ticker_substring_by_file_conts(historic_data_dir,"BTC.csv","/BTCbinance", "-BTC.binance"))
    task3 = asyncio.create_task( change_ticker_substring_by_file_conts(historic_data_dir,"ETH", "/ETHbinance", "-ETH.binance"))
    task4 = asyncio.create_task( change_ticker_substring_by_file_conts(historic_data_dir,"GBP", "/GBPbinance", "-GBP.binance"))
    task5 = asyncio.create_task( change_ticker_substring_by_file_conts(historic_data_dir,"EUR", "/EURbinance", "-EUR.binance"))
    task6 = asyncio.create_task( change_ticker_substring_by_file_conts(historic_data_dir,"TRY", "/TRYbinance", "-TRY.binance"))
    task7 = asyncio.create_task( change_ticker_substring_by_file_conts(historic_data_dir,"USD", "/USDbinance", "-USD.binance"))
    task8 = asyncio.create_task( change_ticker_substring_by_file_conts(historic_data_dir,"BRL", "/BRLbinance", "-BRL.binance"))
    task9 = asyncio.create_task( change_ticker_substring_by_file_conts(historic_data_dir,"BNB", "/BNBbinance", "-BNB.binance"))
    task10 = asyncio.create_task( change_ticker_substring_by_file_conts(historic_data_dir,"JPY","/JPYbinance", "-JPY.binance"))
    task11 = asyncio.create_task( change_ticker_substring_by_file_conts(historic_data_dir,"UAH", "/UAHbinance", "-UAH.binance"))
    task12 = asyncio.create_task( change_ticker_substring_by_file_conts(historic_data_dir,"SOL", "/SOLbinance", "-SOL.binance"))
    task13 = asyncio.create_task( change_ticker_substring_by_file_conts(historic_data_dir,"DAI", "/DAIbinance", "-DAI.binance"))
    task14 = asyncio.create_task( change_ticker_substring_by_file_conts(historic_data_dir,"MXN", "/MXNbinance", "-MXN.binance"))
    task15 = asyncio.create_task( change_ticker_substring_by_file_conts(historic_data_dir,"PLN", "/PLNbinance", "-PLN.binance"))
    task16 = asyncio.create_task( change_ticker_substring_by_file_conts(historic_data_dir,"RON", "/RONbinance", "-RON.binance"))
    task17 = asyncio.create_task( change_ticker_substring_by_file_conts(historic_data_dir,"TUST","/TUSTbinance", "-TUST.binance"))
    task18 = asyncio.create_task( change_ticker_substring_by_file_conts(historic_data_dir,"ZAR", "/ZARbinance", "-ZAR.binance"))

    tasks =[
        task1,
        task2,
        task3,
        task4,
        task5,
        task6,
        task7,
        task8,
        task9,
        task10,
        task11,
        task12,
        task13,
        task14,
        task15,
        task16,
        task17,
        task18,
    ]
    await asyncio.gather(*tasks)
if __name__=="__main__":
    asyncio.run(main())
