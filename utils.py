from matplotlib.dates import DateFormatter
import matplotlib.pyplot as plt
import datetime

def configure_plot(ax, from_date, to_date, selected_currency):
    ax.set_xlabel('Дата')
    ax.set_ylabel(f'Цена закрытия ({selected_currency})')
    ax.set_title('График цены криптовалют')
    ax.legend()
    ax.grid(color='lightgray', linestyle='--')

    date_format = DateFormatter('%d.%m.%y')
    ax.xaxis.set_major_formatter(date_format)
    plt.xticks(rotation=90)

    ax.set_xlim(from_date, to_date + datetime.timedelta(days=1))
