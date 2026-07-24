from typing import Dict, List
import reflex as rx
import httpx
from datetime import date

#====================================Backend=============================================
class State(rx.State):
    table_data: List = []
    columns_table_data: List = ["Date", "Base", "Quote", "Rate"]    
    chart_data: List[Dict] = []

    mode: str = "Latest"
    currency: str = ""    
    client_ip: str = ""

    @rx.event(background=True)
    async def fetch_latest_data(self):
        async with httpx.AsyncClient() as client:                    

            response = await client.get("https://api.frankfurter.dev/v2/rates?base=USD")
            data = response.json()            
            rows = [
                [item["date"], item["base"], item["quote"], item["rate"]]
                for item in data
            ]
            
            async with self:
                self.table_data = []
                self.table_data = rows
                self.mode = "Latest"

    @rx.event(background=True)
    async def fetch_timeseries_data(self):
        async with httpx.AsyncClient() as client:      
            client_ip = self.router.session.client_ip.strip()
            response_client_currency = await client.get(f"http://ip-api.com/csv/{client_ip}?fields=currency")
            client_currency = response_client_currency.text.strip()
            
            # default
            if client_currency == "":
                client_currency = "USD"
            
            if client_currency == "USD":
                base = "EUR"
            else:
                base = "USD"
            
            # last 2 years
            last_year = date.today().replace(year=date.today().year - 2)            

            response = await client.get(f"https://api.frankfurter.dev/v2/rates?from={last_year.strftime('%Y-%m-%d')}&group=month&base={base}&quotes={client_currency}")
            data = response.json()            
            rows = [
                [item["date"], item["base"], item["quote"], item["rate"]]
                for item in data
            ]
                        
            async with self:
                self.table_data = []
                self.table_data = rows     
                self.chart_data = data
                self.mode = "Timeseries"
                self.currency = client_currency if len(response_client_currency.text.strip()) > 0 else "undetected (default USD)"
                self.client_ip = client_ip
                

#====================================Frontend=============================================
def index() -> rx.Component:
    return rx.vstack(
        rx.text(State.mode, font_size="18px", font_weight="bold", margin_bottom="10px"),        
        rx.hstack(
            rx.button("Latest", rx.icon("calendar_search", size=15), on_click=[State.fetch_latest_data, rx.toast.info("Get latest currency rates", duration=5000, position="top-right")], width="120px", cursor="pointer", variant="classic"),
            rx.button("Timeseries", rx.icon("calendar_clock", size=15), on_click=[State.fetch_timeseries_data, rx.toast.warning("Get your currency rate time series from the past 2 years", duration=5000, position="top-right")], width="120px", cursor="pointer", variant="classic"),            
        ),    
        rx.cond(
            State.mode == "Timeseries", 
            rx.callout(f"Based on your IP Address {State.client_ip}, your currency is: {State.currency}", icon="info", variant="surface", width="100%"),
            rx.fragment(),
        ),    
        rx.data_table(
            data=State.table_data,
            columns=State.columns_table_data,            
            pagination=True,
            sort=True,
            search=True,
        ),
        rx.cond(
            State.mode == "Timeseries",            
            rx.recharts.line_chart(
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.x_axis(data_key="date"),
                rx.recharts.y_axis(data_key="rate"),
                rx.recharts.graphing_tooltip(),
                rx.recharts.legend(),
                rx.recharts.line(
                    data_key="rate",
                    type_="monotone",
                ),
                data=State.chart_data,
                width="100%",
                height=400,
            ),                     
            rx.fragment(),
        ),   
        rx.text(f"Based on free api frankfurter.dev and ip-api.com with req/s limitations", font_size="12px"),             
        on_mount=State.fetch_latest_data,
        width="50%",     
        padding="10px",
    ) 

#===================================Render Page===========================================
app = rx.App()
app.add_page(index)
