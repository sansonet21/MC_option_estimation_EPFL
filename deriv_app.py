import tkinter as tk
import adv_prog_proj as deriv
import numpy as np
from tkinter import ttk


class OptionPricingApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Option Pricing Calculator")

        stocks = deriv.get_tickers()

        tk.Label(master, text="Programming Language").grid(row=0)
        self.prog_language = tk.StringVar()
        self.prog_language.set("python")
        self.prog_language_menu = tk.OptionMenu(master, self.prog_language, "python", "C++")
        self.prog_language_menu.grid(row=0, column=1)

        tk.Label(master, text="Stock Ticker").grid(row=1)
        self.selected_stock = tk.StringVar()
        self.selected_stock.set(stocks[0])
        self.ticker_menu = tk.OptionMenu(master, self.selected_stock, *stocks)
        self.ticker_menu.grid(row=1, column=1)

        tk.Label(master, text="Search Ticker:").grid(row=2)
        self.search_entry = ttk.Entry(master)
        self.search_entry.grid(row=2, column=1)
        self.search_entry.bind("<KeyRelease>", self.on_search)

        # create labels and entries
        tk.Label(master, text="T (years)").grid(row=3)
        self.t_entry = tk.Entry(master)
        self.t_entry.grid(row=3, column=1)

        tk.Label(master, text="N (periods within a year)").grid(row=4)
        self.n_entry = tk.Entry(master)
        self.n_entry.grid(row=4, column=1)

        tk.Label(master, text="n (simulations)").grid(row=5)
        self.sim_entry = tk.Entry(master)
        self.sim_entry.grid(row=5, column=1)

        tk.Label(master, text="Parameter estimation period").grid(row=6)
        self.param_est = tk.Entry(master)
        self.param_est.grid(row=6, column=1)

        tk.Label(master, text="Option type").grid(row=7)
        self.option_type = tk.StringVar()
        self.option_type.set('European')
        self.option_menu = tk.OptionMenu(master, self.option_type, 'European', 'American','Asian')
        self.option_menu.grid(row=7, column=1)

        tk.Label(master, text="Strike price").grid(row=8)
        self.k_entry = tk.Entry(master)
        self.k_entry.grid(row=8, column=1)

        tk.Label(master, text="Call/Put").grid(row=9)
        self.call_put = tk.StringVar()
        self.call_put.set("call")
        self.call_put_menu = tk.OptionMenu(master, self.call_put, "call", "put")
        self.call_put_menu.grid(row=9, column=1)

        # create button to calculate price
        self.calculate_button = tk.Button(master, text="Calculate price", command=self.calculate_price)
        self.calculate_button.grid(row=10, columnspan=2)

        # create label to display result
        tk.Label(master, text="Option price:").grid(row=11)
        self.result_label = tk.Label(master, text="")
        self.result_label.grid(row=11, column=1)

        self.error_label = tk.Label(master, fg='red')
        self.error_label.grid(row=12, columnspan=2)

    def on_search(self, event):
        stocks = deriv.get_tickers()
        search_text = self.search_entry.get().upper()
        matched_stocks = [stock for stock in stocks if search_text in stock]
        self.selected_stock.set(matched_stocks[0] if matched_stocks else stocks[0])

    def calculate_price(self):
        # get inputs
        # programming_languge = self.prog_language.get()
        try:
            T = float(self.t_entry.get())
        except:
            self.error_label.config(text='Please enter a valid time to maturity which must be a number')
            print("Please enter a valid time to maturity which must be a number.")
        try:
            N = int(self.n_entry.get())
        except:
            self.error_label.config(text='Please enter a valid integer input for the number of periods within a year.')
            print("Please enter a valid integer input for the number of periods within a year.")
        try:
            n = int(self.sim_entry.get())
        except:
            self.error_label.config(text='Please enter a valid integer input for the number of simulations.')
            print("Please enter a valid integer input for the number of simulations.")
        try:
            K = float(self.k_entry.get())
        except:
            self.error_label.config(text='Please enter a valid numeric input for the strike price.')
            print("Please enter a valid numeric input for the strike price.")
        try:
            time_horizon = float(self.param_est.get())
        except:
            self.error_label.config(text='Please enter a valid time horizon which must be a number.')
            print("Please enter a valid time horizon which must be a number.")
        
        assert n <= 10**5 and n > 0, self.error_label.config(text="Number of simulations must be less than 10^5")

        S0, sigma , mu = deriv.inputs(self.selected_stock.get(), time_horizon)
        self.error_label.config(text='')
        print(S0, sigma, mu)
        if self.option_type.get() == 'European':
                price_val = deriv.price(T=T, N=N, n=n, sigma=sigma, mu=mu, S0=S0, K=K, type=self.call_put.get())
        elif self.option_type.get() == 'Asian':
             type_val = 'asian_'+self.call_put.get()
             price_val = deriv.price(T, N, n, sigma, mu, S0, K, type=type_val)
        elif self.option_type.get() == 'American':
            price_val = deriv.american_price(T, N, n, sigma, mu, S0, K, type=self.call_put.get())



        # calculate option price
        # price_val = deriv.price(T, N, n, sigma, mu, r, S0, K, option_type)
        
        
        self.result_label.config(text="{:.2f}".format(price_val))

if __name__ == '__main__':
    root = tk.Tk()
    ws = OptionPricingApp(root)
    root.mainloop()