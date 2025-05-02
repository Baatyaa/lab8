import requests
import json
import logging
from datetime import datetime
import os


class AtaixOrderMonitor:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.ataix.kz/api"
        self.session = requests.Session()
        self.session.headers.update({
            "accept": "application/json",
            "X-API-Key": self.api_key
        })

        # Логирование қосу
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='order_monitor.log'
        )

        # Нәтижелер бумасы
        os.makedirs("completed_orders", exist_ok=True)

    def get_order(self, order_id):
        """Ордер ақпаратын алу"""
        try:
            response = self.session.get(f"{self.base_url}/orders/{order_id}")
            data = response.json()

            if not data.get('status'):
                logging.error(f"Ордер алу қатесі: {data.get('message')}")
                return None

            return data['result']
        except Exception as e:
            logging.error(f"API қатесі: {str(e)}")
            return None

    def process_completed_order(self, order):
        """Filled ордерді өңдеу және пайданы есептеу"""
        try:
            # Негізгі ақпарат
            order_id = order['orderID']
            symbol = order['symbol']
            side = order['side']
            quantity = float(order['cumQuantity'])

            # Қаржылық мәндер
            quote_amount = float(order['cumQuoteQuantity'])
            commission = float(order['cumCommission'])

            # Пайданы есептеу
            if side.lower() == 'sell':
                net_profit = quote_amount - commission
                profit_percentage = (net_profit / (quote_amount + commission)) * 100
            else:
                net_profit = 0  # Сатып алу ордері үшін пайда жоқ
                profit_percentage = 0

            # JSON файлға сақталатын деректер
            result_data = {
                "order_info": {
                    "order_id": order_id,
                    "symbol": symbol,
                    "side": side,
                    "status": order['status'],
                    "executed_quantity": quantity,
                    "timestamp": datetime.now().isoformat()
                },
                "financials": {
                    "total_amount": quote_amount,
                    "commission": commission,
                    "net_profit_usdt": round(net_profit, 6),
                    "profit_percentage": round(profit_percentage, 2)
                }
            }

            # Файлға сақтау
            filename = f"completed_orders/{order_id}_{datetime.now().strftime('%Y%m%d')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)

            logging.info(f"Ордер өңделді: {order_id} | Пайда: {profit_percentage}%")
            return result_data

        except Exception as e:
            logging.error(f"Ордерді өңдеу қатесі: {str(e)}")
            return None

    def monitor_orders(self, order_ids):
        """Ордерлерді мониторинг жасау"""
        results = []

        for order_id in order_ids:
            order = self.get_order(order_id)
            if not order:
                continue

            if order.get('status', '').lower() == 'filled':
                result = self.process_completed_order(order)
                if result:
                    results.append(result)

        return results


# Мысал қолдану
if __name__ == "__main__":
    # Конфигурация
    API_KEY = "wHxKGrbUdTRvHLT4Ldjho0PpOCqFEc6bW8tWstnSLAfJi0uu7aZFJWlhzkp2Un43zmgrTp0pVQskg7GKFHJJ4n"
    ORDER_IDS = [
        "LTC-USDT-65712-1746209681834",
        "ETH-USDT-78901-1746212345678"
    ]

    # Мониторды іске қосу
    monitor = AtaixOrderMonitor(API_KEY)

    # Ордерлерді тексеру
    results = monitor.monitor_orders(ORDER_IDS)

    # Нәтижелерді көрсету
    print("Өңделген ордерлер:")
    print(json.dumps(results, indent=2, ensure_ascii=False))