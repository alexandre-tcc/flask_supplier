import csv
from datetime import datetime
import pandas as pd
import dash
import random
import base64
from dash import html
from dash_table import DataTable
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
from flask import Flask, request, session, redirect
import plotly.express as px
import io

import string

import os
from flask_login import login_user, LoginManager, UserMixin, logout_user, current_user
from dash.exceptions import PreventUpdate

from flask_session import Session
import uuid

image_filename = 'logo.png'
encoded_image = base64.b64encode(open(image_filename, 'rb').read())

# fonts
title_size = 24
body_size = 16

# styles
button_style = {'margin': '20px 20px 20px 20px', 'fontSize': 18, 'font-family': 'sans-serif'}

# icons
add_icon = html.I(className="fa-regular fa-floppy-disk me-2")
clear_icon = html.I(className="fa-solid fa-trash me-2")
change_icon = html.I(className="fa-solid fa-wrench me-2")
warning_icon = html.I(className="fa-solid fa-circle-exclamation me-2")
ok_icon = html.I(className="fa-solid fa-circle-check me-2")
edit_icon = html.I(className="fa-solid fa-floppy-disk me-2")
enter_icon = html.I(className="fa-solid fa-right-to-bracket me-2")
dl_icon = html.I(className="fa-solid fa-download me-2")
new_icon = html.I(className="fa-sharp fa-solid fa-plus")
rank_icon = html.I(className="fa-solid fa-ranking-star")

VALID_USERNAME_PASSWORD_PAIRS = {
    'tcc1': 'tcc1',
    'tcc2': 'tcc2',
    'tcc3': 'tcc3',
    'accessR17': 'GBHICZs564it',
    'accessT16': '5veIKEcd457d',
}


def clear_database():
    open('save_sup.csv', 'w')


def clear_suppliers(user):
    db_all_users = csv_to_df_clean('save_sup.csv')
    db_without_current_user = db_all_users[db_all_users['username'] != user]
    db_without_current_user.to_csv('save_sup.csv', index=False, header=False)


def generate_random_id():
    letters = string.ascii_uppercase
    digits = string.digits
    random_string = ''.join(random.choice(letters) for _ in range(2))
    random_string += ''.join(random.choice(digits) for _ in range(4))
    return random_string


def reset_weightage():
    with open('param_wt_init.csv', 'r') as input_file:
        reader = csv.reader(input_file)
        rows = list(reader)
    # Create a new CSV file with the same information
    with open('param_wt.csv', 'w', newline='') as output_file:
        writer = csv.writer(output_file)
        for row in rows:
            writer.writerow(row)


def DL_ranking(df):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1', index=False)
    writer.save()
    return output.getvalue()


def check_duplicate(name):
    tag_ = False
    with open('save_sup.csv', 'r') as f:
        datareader = csv.reader(f)
        for row_test in datareader:
            if row_test != []:
                if row_test[1] == name:
                    tag_ = True
    return tag_


def test_length(name_file):
    length = 0
    with open(name_file, 'r') as f:
        datareader = csv.reader(f)
        for row_test in datareader:
            if row_test != []:
                length += 1
    if length >= 25:
        return False
    else:
        return True


def csv_to_df_live(name_file,
                   scf_wt,
                   VMI_wt,
                   critical_wt,
                   inventory_wt,
                   pay_term_wt,
                   lead_time_wt,
                   business_wt,
                   overdue_wt):
    data = []
    with open(name_file, 'r') as f:
        datareader = csv.reader(f)
        for row_test in datareader:
            if row_test != []:
                data.append(row_test)

    # LET'S HAVE A CREATED DATA WITH SCORE FROM DF_DATA
    data_score = []
    for row in data:
        row_nk = []
        row_nk.append(row[0])
        row_nk.append(weighted_total_live(row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], scf_wt,
                                          VMI_wt,
                                          critical_wt,
                                          inventory_wt,
                                          pay_term_wt,
                                          lead_time_wt,
                                          business_wt,
                                          overdue_wt))
        data_score.append(row_nk)

    df = pd.DataFrame(data_score, columns=['Supplier Name', 'Rating (out of 10)'])
    sorted_df = df
    sorted_df['Rating (out of 10)'] = sorted_df['Rating (out of 10)'].astype(float)
    sorted_df['ReverseRank'] = sorted_df['Rating (out of 10)'].rank(method='max')
    nrows = sorted_df.shape[0]
    max_rank = sorted_df['ReverseRank'].max()
    sorted_df['Rank'] = nrows + 1 - df['ReverseRank']
    sorted_df.pop('ReverseRank')
    sorted_df = sorted_df.sort_values('Rating (out of 10)', ascending=False)
    sorted_df.insert(0, 'Rank', sorted_df.pop('Rank'))

    return sorted_df


def check_data_user(user_, data_):
    data_filtered_ = []
    for row in data_:
        if row[0] == user_:
            data_filtered_.append(row)
    return data_filtered_


def csv_to_df(name_file, user_):
    data = []
    with open(name_file, 'r') as f:
        datareader = csv.reader(f)
        for row_test in datareader:
            if row_test != []:
                data.append(row_test)

    data_user = check_data_user(user_, data)

    # LET'S HAVE A CREATED DATA WITH SCORE FROM DF_DATA
    data_score = []
    for row in data_user:
        row_nk = []
        row_nk.append(row[1])
        row_nk.append(weighted_total(row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]))
        row_nk.append(row[2])
        data_score.append(row_nk)

    df = pd.DataFrame(data_score, columns=['Supplier Name', 'Rating (out of 10)', 'Amount'])
    sorted_df = df
    sorted_df['Rating (out of 10)'] = sorted_df['Rating (out of 10)'].astype(float)
    sorted_df['ReverseRank'] = sorted_df['Rating (out of 10)'].rank(method='max')
    nrows = sorted_df.shape[0]
    max_rank = sorted_df['ReverseRank'].max()
    sorted_df['Rank'] = nrows + 1 - df['ReverseRank']
    sorted_df.pop('ReverseRank')
    sorted_df = sorted_df.sort_values('Rating (out of 10)', ascending=False)
    sorted_df.insert(0, 'Rank', sorted_df.pop('Rank'))

    return sorted_df


def csv_to_df_2(name_file_, user_):
    data = []
    with open(name_file_, 'r') as f:
        datareader = csv.reader(f)
        for row_test in datareader:
            if row_test != []:
                data.append(row_test)

    data_user = check_data_user(user_, data)

    # LET'S HAVE A CREATED DATA WITH SCORE FROM DF_DATA
    data_score = []
    for row in data_user:
        row_nk = []
        row_nk.append(row[1])
        row_nk.append(weighted_total(row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]))
        row_nk.append(row[2])
        row_nk.append(row[3])
        row_nk.append(row[4])
        row_nk.append(row[5])
        row_nk.append(row[6])
        row_nk.append(row[7])
        row_nk.append(row[8])
        row_nk.append(row[9])
        row_nk.append(row[10])
        data_score.append(row_nk)

    df = pd.DataFrame(data_score,
                      columns=['Supplier Name', 'Rating (out of 10)', 'Amount ($M)', 'Criteria 1', 'Criteria 2',
                               'Criteria 3', 'Criteria 4', 'Criteria 5', 'Criteria 6', 'Criteria 7',
                               'Criteria 8']).set_index('Supplier Name')
    # df = pd.DataFrame(data_score, columns = ['Supplier Name','Rating (out of 10)'])
    sorted_df = df
    sorted_df['Rating (out of 10)'] = sorted_df['Rating (out of 10)'].astype(float)
    sorted_df['ReverseRank'] = sorted_df['Rating (out of 10)'].rank(method='max')
    nrows = sorted_df.shape[0]
    max_rank = sorted_df['ReverseRank'].max()
    sorted_df['Rank'] = nrows + 1 - df['ReverseRank']
    sorted_df['Rank'] = sorted_df['Rank'].astype(int)
    sorted_df.pop('ReverseRank')
    sorted_df.insert(1, 'Responses', ' ')
    sorted_df = sorted_df.sort_values('Rating (out of 10)', ascending=False)
    sorted_df.insert(0, 'Rank', sorted_df.pop('Rank'))
    sorted_df = sorted_df.T.reset_index()
    sorted_df.rename(columns={'index': 'Supplier'}, inplace=True)

    return sorted_df


def csv_to_df_clean(name_file_):
    data = []
    with open(name_file_, 'r') as f:
        datareader = csv.reader(f)
        for row_test in datareader:
            if row_test != []:
                data.append(row_test)

    # LET'S HAVE A CREATED DATA WITH SCORE FROM DF_DATA
    data_score = []
    for row in data:
        row_nk = []
        row_nk.append(row[0])
        row_nk.append(row[1])
        row_nk.append(row[2])
        row_nk.append(row[3])
        row_nk.append(row[4])
        row_nk.append(row[5])
        row_nk.append(row[6])
        row_nk.append(row[7])
        row_nk.append(row[8])
        row_nk.append(row[9])
        row_nk.append(row[10])
        row_nk.append(row[11])
        data_score.append(row_nk)

    df = pd.DataFrame(data_score,
                      columns=['username', 'Supplier Name', 'Amount ($M)', 'Criteria 1', 'Criteria 2', 'Criteria 3',
                               'Criteria 4', 'Criteria 5', 'Criteria 6', 'Criteria 7', 'Criteria 8', 'id'])

    return df


def csv_to_df_raw(name_file, user_):
    data = []
    with open(name_file, 'r') as f:
        datareader = csv.reader(f)
        for row_test in datareader:
            if row_test != []:
                data.append(row_test)

    data_user = check_data_user(user_, data)

    data_score = []
    for row in data_user:
        row_nk = []
        row_nk.append(row[1])
        row_nk.append(weighted_total(row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]))
        data_score.append(row_nk)

    df = pd.DataFrame(data_score, columns=['Supplier Name', 'Rating (out of 10)'])

    return df


def csv_to_df_data(name_file, user_):
    data = []
    with open(name_file, 'r') as f:
        datareader = csv.reader(f)
        for row_test in datareader:
            if row_test != []:
                data.append(row_test)

    data_user = check_data_user(user_, data)

    df = pd.DataFrame(data_user,
                      columns=['user', 'Supplier Name', 'amount', 'scf', 'VMI', 'critical', 'inventory', 'pay_term',
                               'lead_time', 'business', 'overdue', 'id'])
    df_r = df.drop('user', axis=1)
    return df_r


def del_sup(id_, file_name='save_sup.csv'):
    data = []
    data_new = []

    with open(file_name, 'r') as f:
        datareader = csv.reader(f)
        for row_test in datareader:
            if row_test != []:
                data.append(row_test)

    open(file_name, 'w')

    for row_b in data:
        if row_b[-1] != id_:
            data_new.append(row_b)

    for row_a in data_new:
        with open('save_sup.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow(row_a)


def edit_sup(user,
             name,
             amount_,
             scf_,
             VMI_,
             critical_,
             inventory_,
             pay_term_,
             lead_time_,
             business_,
             overdue_,
             id_,
             file_name='save_sup.csv'):
    data = []
    data_new = []

    with open(file_name, 'r') as f:
        datareader = csv.reader(f)
        for row_test in datareader:
            if row_test != []:
                data.append(row_test)

    open(file_name, 'w')
    # aziza de sie
    for row_b in data:
        if row_b[11] == id_:
            data_new.append([user,
                             name,
                             amount_,
                             scf_,
                             VMI_,
                             critical_,
                             inventory_,
                             pay_term_,
                             lead_time_,
                             business_,
                             overdue_,
                             id_])
        else:
            data_new.append(row_b)

    for row_a in data_new:
        with open('save_sup.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow(row_a)


class Supplier:
    def __init__(self, name_, amount_, scf_,
                 VMI_,
                 critical_,
                 inventory_,
                 pay_term_,
                 lead_time_,
                 business_,
                 overdue_):
        self.name_ = name_
        self.amount_ = amount_
        self.scf_ = scf_
        self.VMI_ = VMI_
        self.critical_ = critical_
        self.inventory_ = inventory_
        self.pay_term_ = pay_term_
        self.lead_time_ = lead_time_
        self.business_ = business_
        self.overdue_ = overdue_

    def add_supplier(self, user_):
        test_length = False
        with open('save_sup.csv', 'r') as f:
            datareader = csv.reader(f)
            for row_test in datareader:
                if row_test != []:
                    if row_test[0] == self.name_:
                        test_id = True

        if test_length == False:
            id_sup = generate_random_id()
            row = [user_, self.name_, self.amount_, self.scf_, self.VMI_, self.critical_, self.inventory_,
                   self.pay_term_, self.lead_time_, self.business_, self.overdue_, id_sup]
            with open('save_sup.csv', 'a') as f:
                writer = csv.writer(f)
                writer.writerow(row)
                # print('Supplier : '+self.name_+'  Added')

    def save_add_tcc(self, user_):
        row = [user_, datetime.now(), self.name_, self.amount_, self.scf_, self.VMI_, self.critical_, self.inventory_,
               self.pay_term_, self.lead_time_, self.business_, self.overdue_]
        with open('historic_save.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow(row)


def generate_color_code(value):
    max_ = 10
    percent = (value - 1) / (max_ - 1) * 100
    # calculate the red and green values based on the percentage
    red = int(255 * (100 - percent) / 100)
    green = int(255 * percent / 100)
    # format the color code as a hex string
    color_code = '#{:02x}{:02x}00'.format(red, green)
    return color_code


def weighted_total(name_,
                   amount_,
                   scf_,
                   VMI_,
                   critical_,
                   inventory_,
                   pay_term_,
                   lead_time_,
                   business_,
                   overdue_, ):
    if any([arg is None for arg in [name_,
                                    amount_,
                                    scf_,
                                    VMI_,
                                    critical_,
                                    inventory_,
                                    pay_term_,
                                    lead_time_,
                                    business_,
                                    overdue_, ]]) or name_ == '':
        # print('there is none')
        return -1

    else:

        df_wt = pd.read_csv('param_wt.csv', header=0)
        scf_wt = df_wt['scf'][0]
        VMI_wt = df_wt['VMI'][0]
        critical_wt = df_wt['critical'][0]
        inventory_wt = df_wt['inventory'][0]
        pay_term_wt = df_wt['pay_term'][0]
        lead_time_wt = df_wt['lead_time'][0]
        business_wt = df_wt['business'][0]
        overdue_wt = df_wt['overdue'][0]

        # print(scf_wt+VMI_wt+critical_wt+inventory_wt+pay_term_wt+lead_time_wt+business_wt+overdue_wt)

        if scf_wt + VMI_wt + critical_wt + inventory_wt + pay_term_wt + lead_time_wt + business_wt + overdue_wt > 1:
            # print('>1')
            return -1

        else:
            # ----------------------------------------scf
            if scf_ == 'No':
                scf = 10 * scf_wt
            else:
                scf = 0

            # ----------------------------------------VMI
            if VMI_ == 'No':
                VMI = 10 * VMI_wt
            else:
                VMI = 0

            # ----------------------------------------critical
            if critical_ == 'Yes':
                critical = 10 * critical_wt
            else:
                critical = 0

            # ----------------------------------------inventory
            if inventory_ == 'Yes':
                inventory = 10 * inventory_wt
            else:
                inventory = 0

            # ----------------------------------------pay_term
            if pay_term_ == 'No':
                pay_term = 10 * pay_term_wt
            else:
                pay_term = 0

            # ----------------------------------------lead_time
            if lead_time_ == 'Yes':
                lead_time = 10 * lead_time_wt
            else:
                lead_time = 0

            # ----------------------------------------business
            if business_ == 'Yes':
                business = 10 * business_wt
            else:
                business = 0

            # ----------------------------------------overdue
            if overdue_ == 'No':
                overdue = 10 * overdue_wt
            else:
                overdue = 0

            return (scf + VMI + critical + inventory + pay_term + lead_time + business + overdue)


def weighted_total_live(name_,
                        scf_,
                        VMI_,
                        critical_,
                        inventory_,
                        pay_term_,
                        lead_time_,
                        business_,
                        overdue_,
                        scf_wt,
                        VMI_wt,
                        critical_wt,
                        inventory_wt,
                        pay_term_wt,
                        lead_time_wt,
                        business_wt,
                        overdue_wt):
    if any([arg is None for arg in [name_,
                                    scf_,
                                    VMI_,
                                    critical_,
                                    inventory_,
                                    pay_term_,
                                    lead_time_,
                                    business_,
                                    overdue_, ]]):
        return -1

    else:
        totall = scf_wt + VMI_wt + critical_wt + inventory_wt + pay_term_wt + lead_time_wt + business_wt + overdue_wt
        if totall != 100:
            return -1

        else:
            # ----------------------------------------scf
            if scf_ == 'No':
                scf = 10 * scf_wt / 100
            else:
                scf = 0

            # ----------------------------------------VMI
            if VMI_ == 'No':
                VMI = 10 * VMI_wt / 100
            else:
                VMI = 0

            # ----------------------------------------critical
            if critical_ == 'Yes':
                critical = 10 * critical_wt / 100
            else:
                critical = 0

            # ----------------------------------------inventory
            if inventory_ == 'Yes':
                inventory = 10 * inventory_wt / 100
            else:
                inventory = 0

            # ----------------------------------------pay_term
            if pay_term_ == 'No':
                pay_term = 10 * pay_term_wt / 100
            else:
                pay_term = 0

            # ----------------------------------------lead_time
            if lead_time_ == 'Yes':
                lead_time = 10 * lead_time_wt / 100
            else:
                lead_time = 0

            # ----------------------------------------business
            if business_ == 'Yes':
                business = 10 * business_wt / 100
            else:
                business = 0

            # ----------------------------------------overdue
            if overdue_ == 'Yes':
                overdue = 10 * overdue_wt / 100
            else:
                overdue = 0

            return (scf + VMI + critical + inventory + pay_term + lead_time + business + overdue)


def bar_sup(user_):
    df = csv_to_df('save_sup.csv', user_)

    nb_sup = df.shape[0]

    col11 = px.bar(df, x='Rating (out of 10)', y='Supplier Name', barmode='group', text_auto=True, orientation='h',
                   height=150 + nb_sup * 150,
                   color_discrete_sequence=['#FFA41B'])

    # col11.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    col11.update_annotations(font_size=22)

    col11.update_layout(legend=dict(
        orientation="h",
        title=None,
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(
            size=18,
            color="black"
        ),
    ))

    col11.update_traces(textangle=0)

    col11.update_traces(width=0.3)

    col11.update_layout({"bargap": 0.3, 'bargroupgap': 0.12})

    col11.update_layout(xaxis=dict(tickfont=dict(size=18)))

    col11.update_layout(font=dict(size=18))

    col11.update_layout(yaxis=dict(autorange="reversed"))

    return col11


def quadrant(user_):
    df = csv_to_df('save_sup.csv', user_)

    df['Amount'] = df['Amount'].astype(int)
    df['color'] = 'red'

    # Create scatter plot
    fig = px.scatter(df, x='Amount', y='Rating (out of 10)', size='Amount', color_discrete_sequence=['#FFA41B'],
                     text="Supplier Name",
                     labels={"Amount": "Annual spend ($M)", "Rating (out of 10)": "TCC Supplier Rating"},
                     template="simple_white", height=1000, size_max=40)

    # Set quadrant boundaries
    hline_value = (int(max(df['Amount'])) + int(min(df['Amount']))) / 2
    vline_value = 5
    fig.update_layout(
        shapes=[
            dict(
                type='line',
                yref='paper', y0=0, y1=1,
                xref='x', x0=hline_value, x1=hline_value,
                line=dict(color='black', width=2)
            ),
            dict(
                type='line',
                xref='paper', x0=0, x1=1,
                yref='y', y0=vline_value, y1=vline_value,
                line=dict(color='black', width=2)
            )
        ]
    )

    fig.update_yaxes(range=[0, 10])

    # Add annotations
    annotations = []

    annotations.append(
        dict(
            x=0.15,
            y=0.25,
            xref='paper',
            yref='paper',
            text='Low priority',
            showarrow=False,
            font=dict(size=32, color='red'),
            opacity=0.24
        )
    )

    annotations.append(
        dict(
            x=0.10,
            y=0.85,
            xref='paper',
            yref='paper',
            text='Medium priority',
            showarrow=False,
            font=dict(size=32, color='blue'),
            opacity=0.24
        )
    )

    annotations.append(
        dict(
            x=0.90,
            y=0.25,
            xref='paper',
            yref='paper',
            text='Medium priority',
            showarrow=False,
            font=dict(size=32, color='blue'),
            opacity=0.24
        )
    )

    annotations.append(
        dict(
            x=0.85,
            y=0.85,
            xref='paper',
            yref='paper',
            text='High priority',
            showarrow=False,
            font=dict(size=32, color='green'),
            opacity=0.24
        )
    )

    fig.update_layout(
        coloraxis_colorbar=dict(showticklabels=False),
        annotations=annotations
    )

    # Format text above the bubbles
    fig.update_traces(
        texttemplate='%{text}',
        textposition='top center',
        textfont=dict(size=18),
        hovertemplate='Supplier: %{text}<br>Amount: $%{x}M<br>TCC Supplier Rating: %{y}<br>'
    )

    return fig


login = html.Div(
    [
        dcc.Location(id="url_login", refresh=True),

        html.Div(
            children=[
                html.Br(),
                html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()), style={
                    "display": "block",
                    "margin-left": "auto",
                    "margin-right": "auto",
                }),
                html.Br(),
                html.H1('Supplier selection tool - 1TCC © 2023',
                        style={'color': 'white',  # 'pading':'50px 0px 50px 0px',
                               'textAlign': 'center', 'font-family': 'sans-serif', 'fontSize': title_size, }),
                html.Br(),
            ]
            , style={'background-color': 'rgb(52, 56, 52)'}
        ),

        html.Div(children=[

            html.H1(children='Please Login to access the app'),
            html.Br(),
            html.Div(children=[
                html.Label('Username:'),
                dbc.Input(placeholder="Enter your username", type="text", id="uname-box"),
            ]),
            html.Br(),
            html.Div(children=[
                html.Label('Password:'),
                dbc.Input(placeholder="Enter your password", type="password", id="pwd-box"),
            ]),
            html.Br(),
            dbc.Button(children="Login", n_clicks=0, type="submit", id="login-button", style=button_style),
            # html.Div(id='login-status'),

            html.Br(),

            html.Div(children=["Don't have access? ",
                               html.A("Contact 1TCC to get access", href="https://1tcc.com/tcc-contact/",
                                      target="_blank")]),

            html.Br(),
            html.Br(),
            html.Br(),
            html.Div(children=[dcc.Link("Home", href="/"), ]),

        ], style={

            "display": "flex",
            "flex-direction": "column",
            "justify-content": "center",
            "align-items": "center",
        }),

        html.Div(children="", id="output-state"),
        html.Br(),

    ], style={'background-color': 'rgb(52, 56, 52)', "height": "100vh", 'width': '100%',
              'display': 'inline-block', 'align-items': 'center', 'horizontalAlign': 'center'}
)

# Successful login
success = html.Div(
    [
        html.Div(
            [
                html.H2("Login successful."),
                html.Br(),
                dcc.Link("Home", href="/"),
            ]
        )
    ]
)

# Failed Login
failed = html.Div(
    [
        html.Div(
            [
                html.H2("Log in Failed. Please try again."),
                html.Br(),
                html.Div([login]),
                dcc.Link("Home", href="/"),
            ]
        )
    ]
)

# logout
logout = html.Div(
    [
        html.Div(html.H2("You have been logged out - Please login")),
        html.Br(),
        dcc.Link("Home", href="/"),
    ]
)

index_page_loggedin = html.Div(
    [
        html.Div(
            children=[
                html.Br(),
                html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()), style={
                    "display": "block",
                    "margin-left": "auto",
                    "margin-right": "auto",
                }),
                html.Br(),
                html.H1('Welcome to 1TCC Supplier selection tool',
                        style={'color': 'white',  # 'pading':'50px 0px 50px 0px',
                               'textAlign': 'center', 'font-family': 'sans-serif', 'fontSize': title_size, }),
                html.Br(),
            ]
            , style={'background-color': 'rgb(52, 56, 52)'}
        ),

        html.Div(children=[

            html.Br(),
            html.Div(
                children=[
                    dbc.Button(
                        "Enter the App",
                        href="/Dashboard",
                        style=button_style
                    )
                ]),
            html.Br(),
            html.Div(
                children=[
                    dcc.Link("logout", href="/logout"),

                ]),

        ], style={

            "display": "flex",
            "flex-direction": "column",
            "justify-content": "center",
            "align-items": "center",
        }),

    ], style={'background-color': 'rgb(52, 56, 52)', "height": "100vh", 'width': '100%',
              'display': 'inline-block', 'align-items': 'center', 'horizontalAlign': 'center'}
)

index_page_loggedout = html.Div(
    [
        html.Div(
            children=[
                html.Br(),
                html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()), style={
                    "display": "block",
                    "margin-left": "auto",
                    "margin-right": "auto",
                }),
                html.Br(),
                html.H1('Welcome to 1TCC Supplier selection tool',
                        style={'color': 'white',  # 'pading':'50px 0px 50px 0px',
                               'textAlign': 'center', 'font-family': 'sans-serif', 'fontSize': title_size, }),
                html.Br(),
            ]
            , style={'background-color': 'rgb(52, 56, 52)'}
        ),

        html.Div(children=[

            html.Div(
                children=[
                    dbc.Button(
                        "Login",
                        href="/login",
                        style=button_style
                    )

                ]),

        ], style={

            "display": "flex",
            "flex-direction": "column",
            "justify-content": "center",
            "align-items": "center",
        }),

    ], style={'background-color': 'rgb(52, 56, 52)', "height": "100vh", 'width': '100%',
              'display': 'inline-block', 'align-items': 'center', 'horizontalAlign': 'center'}
)

Dashboard_layout = html.Div([

    html.Div(children=[

        html.Div(children=[
            html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode())),
        ], style={'verticalAlign': 'top',
                  'margin': '10px',
                  'align-items': 'center', 'flex': 1,
                  'display': 'flex', 'justify-content': 'left'}),

        html.Div(children=[
            dbc.Row(
                html.H3('Supplier Selection Tool', style={'color': 'white', 'font-family': 'sans-serif',
                                                          'fontSize': 45, 'verticalAlign': 'top',
                                                          'display': 'inline-block',
                                                          'align-items': 'center', 'justify-content': 'left'}),
            ),

        ], style={'verticalAlign': 'top',
                  'margin': '10px',
                  'align-items': 'center', 'flex': 1,
                  'display': 'flex', 'justify-content': 'center'}),

        html.Div(
            children=[

                html.Div(
                    children=[
                        dbc.Row(
                            dbc.Button(
                                "Logout",
                                href="/logout",
                                style=button_style
                            )
                        ),
                    ], style={'padding': '0px 50px 0px500px', 'margin': '0px 50px 0px 50px'}
                ),

            ], style={'verticalAlign': 'top',
                      'margin': '10px',
                      'align-items': 'center', 'flex': 1,
                      'display': 'flex', 'justify-content': 'right'}),

    ], style={'background-color': 'rgb(52, 56, 52)', 'display': 'flex',
              'flex': 'row', 'horizontalAlign': 'center', 'height': '120px'}, ),

    # Overall Summary
    dcc.Tabs(
        id="tabs_common_summary",
        className='custom-tabs', vertical=False,
        children=[
            dcc.Tab(label='➲ Criteria responses', value='tab_1', className='custom-tab',
                    selected_className='custom-tab--selected',
                    style={'color': 'white', 'background-color': 'rgb(117, 125, 120)', 'font-family': 'sans-serif'}),
            dcc.Tab(label='☷ Ranking', value='tab_3', className='custom-tab',
                    selected_className='custom-tab--selected',
                    style={'color': 'white', 'background-color': 'rgb(117, 125, 120)', 'font-family': 'sans-serif'}),
            dcc.Tab(label='✎ Edit or remove Supplier', value='tab_4', className='custom-tab',
                    selected_className='custom-tab--selected',
                    style={'color': 'white', 'background-color': 'rgb(117, 125, 120)', 'font-family': 'sans-serif'}),
            # dcc.Tab(label='⚙ Criteria weightage', value='tab_2', className='custom-tab',
            #        selected_className='custom-tab--selected',style={'color': 'white','background-color':'rgb(117, 125, 120)','font-family':'sans-serif'}),
        ],
        style={'font-family': 'sans-serif', 'fontSize': 25, 'color': 'red', 'height': '75px', 'align-items': 'center'}),

    html.Div(children=[

        html.Div(id='tab_display'),

        # FOOTER
        html.Footer(
            children=[
                html.Br(),
                html.H1('1TCC © 2023', style={'color': 'white',  # 'pading':'50px 0px 50px 0px',
                                              'textAlign': 'center', 'font-family': 'sans-serif', 'fontSize': 20, }),
                html.Br(),

            ]
            , style={'background-color': 'rgb(52, 56, 52)', "width": "100%"}

        ),

        # Closing
    ],
        style={'text-align': 'center', 'display': 'inline-block', 'width': '100%',
               'background-color': 'rgb(245, 245, 245)', 'color': 'rgb(79, 79, 79)'})
])

# User status management views

secret_key = 'JptBztlj247parTettL7573'

# Login screen


# Exposing the Flask Server to enable configuring it for logging in
server = Flask(__name__)
app = dash.Dash(
    __name__,
    server=server,
    title="1TCC Supplier Selection",
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.MINTY, dbc.icons.FONT_AWESOME, dbc.icons.BOOTSTRAP]
)

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        dcc.Location(id="redirect", refresh=True),
        html.Div(id="page-content"),
    ]
)

# Updating the Flask Server configuration with Secret Key to encrypt the user session cookie
server.config.update(SECRET_KEY=secret_key)

# Configure Flask-Session for session management
server.config['SESSION_TYPE'] = 'filesystem'  # Choose a session storage type
server.config['SESSION_FILE_DIR'] = './flask_session_cache'
Session(server)

# Login manager object will be used to login / logout users
login_manager = LoginManager()
login_manager.init_app(server)


# User data model. It has to have at least self.id as a minimum
class User(UserMixin):
    def __init__(self, username):
        self.id = username


@login_manager.user_loader
def load_user(username):
    """This function loads the user by user id.
    Typically this looks up the user from a user database.
    We won't be registering or looking up users in this example,
    since we'll just login using an LDAP server.
    So we'll simply return a User object with the passed-in username.
    """
    return User(username)


@app.callback(
    Output("page-content", "children"),
    Output("redirect", "pathname"),
    [Input("url", "pathname")],
    prevent_initial_call=True,
)
def display_page(pathname):
    """Callback to determine the layout to return.
    We need to determine two things every time the user navigates:
    Can they access this page? If so, we just return the view.
    Otherwise, if they need to be authenticated first,
    we need to redirect them to the login page.
    So we have two outputs: the first is the view to return,
    and the second is the redirection to another page if needed.
    """
    # Defaults: view and redirect URL
    view = None
    redirect_url = dash.no_update

    if pathname == "/login":
        view = login
    elif pathname == "/success":
        if current_user.is_authenticated:
            view = success
            redirect_url = "/"
        else:
            view = failed
            redirect_url = "/login"
    elif pathname == "/logout":
        if current_user.is_authenticated:
            logout_user()
            view = logout
            redirect_url = "/login"
        else:
            view = login

    elif pathname == "/Dashboard":
        if current_user.is_authenticated:
            view = Dashboard_layout
        else:
            view = login
            redirect_url = "/login"
    else:
        if current_user.is_authenticated:
            view = index_page_loggedin
        else:
            view = index_page_loggedout

    return view, redirect_url


@app.callback(
    Output("user-status-div", "children"),
    Output("login-status", "data"),
    [Input("url", "pathname")],
)
def login_status(url):
    """Callback to display login/logout link in the header."""
    if (
            hasattr(current_user, "is_authenticated")
            and current_user.is_authenticated
            and url != "/logout"
    ):
        return dcc.Link("logout", href="/logout"), current_user.get_id()
    else:
        return dcc.Link("login", href="/login"), "loggedout"


@app.callback(
    [Output("url_login", "pathname"), Output("output-state", "children")],
    [Input("login-button", "n_clicks")],
    [State("uname-box", "value"), State("pwd-box", "value")],
)
def login_button_click(n_clicks, username, password):
    if n_clicks > 0:
        # if username == "test" and password == "test":
        if username in VALID_USERNAME_PASSWORD_PAIRS and password == VALID_USERNAME_PASSWORD_PAIRS[username]:
            user = User(username)
            login_user(user)
            session['session_active'] = True
            session['session_id'] = str(uuid.uuid4())
            session['session_user'] = username
            return "/success", ""
        else:
            return "/login", "Incorrect username or password"


@app.callback(
    Output('tab_display', 'children'),
    Input('tabs_common_summary', 'value'),
    # Input(df_timeline_CF)
)
def update_styles(tab):
    user_ = session["session_user"]
    if tab == 'tab_1':

        return html.Div(children=[

            html.Div(children=[

                html.H3('Criteria response form', style={'color': 'black', 'font-family': 'sans-serif', 'width': '100%',
                                                         'fontSize': title_size, 'verticalAlign': 'top',
                                                         'margin': '20px 20px 20px 20px',
                                                         'display': 'inline-block', 'horizontalAlign': 'center'}),

                html.Br(),  # ---------Name

                html.Div(children=[

                    html.H3('Name of the supplier:', style={'color': 'black', 'font-family': 'sans-serif',
                                                            'fontSize': body_size, 'verticalAlign': 'top',
                                                            'width': '40%',
                                                            'margin': '10px',
                                                            'align-items': 'center', 'flex': 1,
                                                            'display': 'flex', 'justify-content': 'right'}),

                    dbc.Input(id="name", placeholder="Enter supplier name", type='text',
                              style={'color': 'blue', 'width': '20%', 'font-family': 'sans-serif',
                                     'fontSize': body_size, 'margin': '10px', 'width': '250px',
                                     'align-items': 'center', 'flex': 1,
                                     'display': 'flex', 'justify-content': 'left'}
                              ),
                ], style={'border': 'px solid orange', 'background-color': 'white', 'display': 'flex',
                          'border-radius': 20, 'margin': '30px', 'flex': 'row', 'horizontalAlign': 'center'}, ),

                html.Br(),

                html.Br(),  # ---------AMOUNT

                html.Div(children=[
                    html.H3('Annual spend:', style={'color': 'black', 'font-family': 'sans-serif',
                                                    'fontSize': body_size, 'verticalAlign': 'top',
                                                    'margin': '10px',
                                                    'align-items': 'center', 'flex': 1,
                                                    'flex-direction': 'row',
                                                    'width': '50%',
                                                    'display': 'flex', 'justify-content': 'right'}),

                    dbc.Input(id="amount", placeholder="Amount in $M", type='number', min=0,
                              style={'color': 'blue', 'width': '20%', 'font-family': 'sans-serif',
                                     'fontSize': body_size, 'margin': '10px', 'width': '250px',
                                     'align-items': 'center', 'flex': 1,
                                     'display': 'flex', 'justify-content': 'left'}
                              ),

                    html.H3(' ', style={'color': '#737373', 'font-family': 'sans-serif',
                                        'fontSize': body_size, 'verticalAlign': 'top',
                                        'margin': '10px 30px 10px 30px',
                                        'align-items': 'center', 'flex': 1, 'width': '100px',
                                        'display': 'flex', 'justify-content': 'right'}),

                ], style={'border': 'px solid orange', 'background-color': '#f2f2f2', 'display': 'flex',
                          'border-radius': 20, 'margin': '5px 20px 5px 20px', 'flex': 'row',
                          'horizontalAlign': 'center'}, ),

                html.Br(),  # ---------SCF

                html.Div(children=[
                    html.H3('Criteria 1 - Supplier has access to SCF programs',
                            style={'color': 'black', 'font-family': 'sans-serif',
                                   'fontSize': body_size, 'verticalAlign': 'top',
                                   'margin': '10px',
                                   'align-items': 'center', 'flex': 1,
                                   'flex-direction': 'row',
                                   'width': '50%',
                                   'display': 'flex', 'justify-content': 'right'}),

                    dcc.RadioItems(id='scf', options={'Yes': ' Yes', 'No': ' No'}
                                   , labelStyle={'margin': "10px 20px 10px 20px"},
                                   style={'color': '#3384BA', 'font-family': 'sans-serif', 'width': '25%',
                                          'fontSize': body_size, 'margin': '10px',
                                          'align-items': 'center', 'flex': 1,
                                          'display': 'flex', 'justify-content': 'center'}),

                    html.H3('(Optimal: No)', style={'color': '#737373', 'font-family': 'sans-serif',
                                                    'fontSize': body_size, 'verticalAlign': 'top',
                                                    'margin': '10px 30px 10px 30px',
                                                    'align-items': 'center', 'flex': 1, 'width': '100px',
                                                    'display': 'flex', 'justify-content': 'right'}),

                ], style={'border': 'px solid orange', 'background-color': '#f2f2f2', 'display': 'flex',
                          'border-radius': 20, 'margin': '5px 20px 5px 20px', 'flex': 'row',
                          'horizontalAlign': 'center'}, ),

                html.Br(),  # ---------VMI

                html.Div(children=[
                    html.H3('Criteria 2 - Supplier offers VMI to clients',
                            style={'color': 'black', 'font-family': 'sans-serif',
                                   'fontSize': body_size, 'verticalAlign': 'top',
                                   'margin': '10px',
                                   'align-items': 'center', 'flex': 1,
                                   'display': 'flex', 'justify-content': 'right'}),

                    dcc.RadioItems(id='VMI', options={'Yes': ' Yes', 'No': ' No'}
                                   , labelStyle={'margin': "10px 20px 10px 20px"},
                                   style={'color': '#3384BA', 'font-family': 'sans-serif', 'width': '20%',
                                          'fontSize': body_size, 'margin': '10px',
                                          'align-items': 'center', 'flex': 1,
                                          'display': 'flex', 'justify-content': 'center'}),
                    html.H3('(Optimal: No)', style={'color': '#737373', 'font-family': 'sans-serif',
                                                    'fontSize': body_size, 'verticalAlign': 'top',
                                                    'margin': '10px 30px 10px 30px',
                                                    'align-items': 'center', 'flex': 1, 'width': '25%',
                                                    'display': 'flex', 'justify-content': 'right'}),

                ], style={'border': 'px solid orange', 'background-color': '#f2f2f2', 'display': 'flex',
                          'border-radius': 20, 'margin': '5px 20px 5px 20px', 'flex': 'row',
                          'horizontalAlign': 'center'}, ),

                html.Br(),  # ---------Critical

                html.Div(children=[
                    html.H3('Criteria 3 - Supplier is critical for client',
                            style={'color': 'black', 'font-family': 'sans-serif',
                                   'fontSize': body_size, 'verticalAlign': 'top',
                                   'margin': '10px',
                                   'align-items': 'center', 'flex': 1,
                                   'display': 'flex', 'justify-content': 'right'}),

                    dcc.RadioItems(id='critical', options={'Yes': ' Yes', 'No': ' No'}
                                   , labelStyle={'margin': "10px 20px 10px 20px"},
                                   style={'color': '#3384BA', 'font-family': 'sans-serif', 'width': '20%',
                                          'fontSize': body_size, 'margin': '10px',
                                          'align-items': 'center', 'flex': 1,
                                          'display': 'flex', 'justify-content': 'center'}),
                    html.H3('(Optimal: Yes)', style={'color': '#737373', 'font-family': 'sans-serif',
                                                     'fontSize': body_size, 'verticalAlign': 'top',
                                                     'margin': '10px 30px 10px 30px',
                                                     'align-items': 'center', 'flex': 1, 'width': '25%',
                                                     'display': 'flex', 'justify-content': 'right'}),

                ], style={'border': 'px solid orange', 'background-color': '#f2f2f2', 'display': 'flex',
                          'border-radius': 20, 'margin': '5px 20px 5px 20px', 'flex': 'row',
                          'horizontalAlign': 'center'}, ),

                html.Br(),  # ---------inventory

                html.Div(children=[
                    html.H3('Criteria 4 - Supplier inventory is within top 25 of total Client inventory',
                            style={'color': 'black', 'font-family': 'sans-serif',
                                   'fontSize': body_size, 'verticalAlign': 'top',
                                   'margin': '10px',
                                   'align-items': 'center', 'flex': 1,
                                   'display': 'flex', 'justify-content': 'right'}),

                    dcc.RadioItems(id='inventory', options={'Yes': ' Yes', 'No': ' No'}
                                   , labelStyle={'margin': "10px 20px 10px 20px"},
                                   style={'color': '#3384BA', 'font-family': 'sans-serif', 'width': '20%',
                                          'fontSize': body_size, 'margin': '10px',
                                          'align-items': 'center', 'flex': 1,
                                          'display': 'flex', 'justify-content': 'center'}),
                    html.H3('(Optimal: Yes)', style={'color': '#737373', 'font-family': 'sans-serif',
                                                     'fontSize': body_size, 'verticalAlign': 'top',
                                                     'margin': '10px 30px 10px 30px',
                                                     'align-items': 'center', 'flex': 1, 'width': '25%',
                                                     'display': 'flex', 'justify-content': 'right'}),

                ], style={'border': 'px solid orange', 'background-color': '#f2f2f2', 'display': 'flex',
                          'border-radius': 20, 'margin': '5px 20px 5px 20px', 'flex': 'row',
                          'horizontalAlign': 'center'}, ),

                html.Br(),  # -----------------------------------------------pay_term

                html.Div(children=[
                    html.H3('Criteria 5 - Payment terms are below 45 days',
                            style={'color': 'black', 'font-family': 'sans-serif',
                                   'fontSize': body_size, 'verticalAlign': 'top',
                                   'margin': '10px',
                                   'align-items': 'center', 'flex': 1,
                                   'display': 'flex', 'justify-content': 'right'}),

                    dcc.RadioItems(id='pay_term', options={'Yes': ' Yes', 'No': ' No'}
                                   , labelStyle={'margin': "10px 20px 10px 20px"},
                                   style={'color': '#3384BA', 'font-family': 'sans-serif', 'width': '20%',
                                          'fontSize': body_size, 'margin': '10px',
                                          'align-items': 'center', 'flex': 1,
                                          'display': 'flex', 'justify-content': 'center'}),
                    html.H3('(Optimal: No)', style={'color': '#737373', 'font-family': 'sans-serif',
                                                    'fontSize': body_size, 'verticalAlign': 'top',
                                                    'margin': '10px 30px 10px 30px',
                                                    'align-items': 'center', 'flex': 1, 'width': '25%',
                                                    'display': 'flex', 'justify-content': 'right'}),

                ], style={'border': 'px solid orange', 'background-color': '#f2f2f2', 'display': 'flex',
                          'border-radius': 20, 'margin': '5px 20px 5px 20px', 'flex': 'row',
                          'horizontalAlign': 'center'}, ),

                html.Br(),  # -----------------------------------------------lead_time

                html.Div(children=[
                    html.H3('Criteria 6 - Lead times are 90+ days',
                            style={'color': 'black', 'font-family': 'sans-serif',
                                   'fontSize': body_size, 'verticalAlign': 'top',
                                   'margin': '10px',
                                   'align-items': 'center', 'flex': 1,
                                   'display': 'flex', 'justify-content': 'right'}),

                    dcc.RadioItems(id='lead_time', options={'Yes': ' Yes', 'No': ' No'}
                                   , labelStyle={'margin': "10px 20px 10px 20px"},
                                   style={'color': '#3384BA', 'font-family': 'sans-serif', 'width': '20%',
                                          'fontSize': body_size, 'margin': '10px',
                                          'align-items': 'center', 'flex': 1,
                                          'display': 'flex', 'justify-content': 'center'}),
                    html.H3('(Optimal: Yes)', style={'color': '#737373', 'font-family': 'sans-serif',
                                                     'fontSize': body_size, 'verticalAlign': 'top',
                                                     'margin': '10px 30px 10px 30px',
                                                     'align-items': 'center', 'flex': 1, 'width': '25%',
                                                     'display': 'flex', 'justify-content': 'right'}),

                ], style={'border': 'px solid orange', 'background-color': '#f2f2f2', 'display': 'flex',
                          'border-radius': 20, 'margin': '5px 20px 5px 20px', 'flex': 'row',
                          'horizontalAlign': 'center'}, ),

                html.Br(),  # -----------------------------------------------business

                html.Div(children=[
                    html.H3('Criteria 7 - Client business is  within top 10 of supplier business',
                            style={'color': 'black', 'font-family': 'sans-serif',
                                   'fontSize': body_size, 'verticalAlign': 'top',
                                   'margin': '10px',
                                   'align-items': 'center', 'flex': 1,
                                   'display': 'flex', 'justify-content': 'right'}),

                    dcc.RadioItems(id='business', options={'Yes': ' Yes', 'No': ' No'}
                                   , labelStyle={'margin': "10px 20px 10px 20px"},
                                   style={'color': '#3384BA', 'font-family': 'sans-serif', 'width': '20%',
                                          'fontSize': body_size, 'margin': '10px',
                                          'align-items': 'center', 'flex': 1,
                                          'display': 'flex', 'justify-content': 'center'}),
                    html.H3('(Optimal: Yes)', style={'color': '#737373', 'font-family': 'sans-serif',
                                                     'fontSize': body_size, 'verticalAlign': 'top',
                                                     'margin': '10px 30px 10px 30px',
                                                     'align-items': 'center', 'flex': 1, 'width': '25%',
                                                     'display': 'flex', 'justify-content': 'right'}),

                ], style={'border': 'px solid orange', 'background-color': '#f2f2f2', 'display': 'flex',
                          'border-radius': 20, 'margin': '5px 20px 5px 20px', 'flex': 'row',
                          'horizontalAlign': 'center'}, ),

                html.Br(),  # -----------------------------------------------overdue

                html.Div(children=[
                    html.H3('Criteria 8 - Supplier Invoices overdue 30+ days',
                            style={'color': 'black', 'font-family': 'sans-serif',
                                   'fontSize': body_size, 'verticalAlign': 'top',
                                   'margin': '10px',
                                   'align-items': 'center', 'flex': 1,
                                   'display': 'flex', 'justify-content': 'right'}),

                    dcc.RadioItems(id='overdue', options={'Yes': ' Yes', 'No': ' No'}
                                   , labelStyle={'margin': "10px 20px 10px 20px"},
                                   style={'color': '#3384BA', 'font-family': 'sans-serif', 'width': '20%',
                                          'fontSize': body_size, 'margin': '10px',
                                          'align-items': 'center', 'flex': 1,
                                          'display': 'flex', 'justify-content': 'center'}),
                    html.H3('(Optimal: No)', style={'color': '#737373', 'font-family': 'sans-serif',
                                                    'fontSize': body_size, 'verticalAlign': 'top',
                                                    'margin': '10px 30px 10px 30px',
                                                    'align-items': 'center', 'flex': 1, 'width': '25%',
                                                    'display': 'flex', 'justify-content': 'right'}),

                ], style={'border': 'px solid orange', 'background-color': '#f2f2f2', 'display': 'flex',
                          'border-radius': 20, 'margin': '5px 20px 5px 20px', 'flex': 'row',
                          'horizontalAlign': 'center'}, ),

                html.Br(),

                html.Br(),

                html.Div(id='supplier_score'),

            ], style={'width': '95%', 'border': 'px solid orange', 'box-shadow': '5px 5px 15px 8px lightgrey',
                      'background-color': 'white', 'display': 'inline-block',
                      'border-radius': 20, 'margin': '50px', 'padding': '50px'}),

            html.Br(), ])

    # --------------------------------------------DECISION REMOVE WEIGHTAGE TAB

    elif tab == 'tab_3':
        return html.Div(dcc.Loading(
            id="supplier_table",
            type="dot",
            className="loading-component",
        ), )

    elif tab == 'tab_4':
        df_ = csv_to_df_raw('save_sup.csv', user_)
        if df_.shape[0] == 0:
            return html.H3('No supplier is currently ranked, go to -- Criteria responses tab and enter responses',
                           style={'color': '#383838', 'font-family': 'sans-serif',
                                  'fontSize': 22, 'verticalAlign': 'top', 'margin': '50px',
                                  'display': 'inline-block', 'horizontalAlign': 'center',
                                  'border': '0px solid orange', 'background-color': 'white', 'display': 'inline-block',
                                  'border-radius': 20, 'horizontalAlign': 'center', 'padding': '50px'}),
        else:
            return html.Div(children=[
                html.H3('Supplier List', style={'color': 'black', 'font-family': 'sans-serif', 'width': '300px',
                                                'fontSize': title_size, 'verticalAlign': 'top', 'margin': '50px',
                                                'display': 'inline-block', 'horizontalAlign': 'center'}),

                html.Br(),

                DataTable(
                    id='datatable-modify',
                    columns=[
                        {"name": i, "id": i, "selectable": True} for i in df_.columns
                    ],
                    data=df_.to_dict('records'),
                    editable=True,
                    style_cell={'padding': '10px', 'font-family': 'sans-serif', 'fontSize': 24},
                    sort_action="native",
                    sort_mode="multi",
                    # style_table={'maxWidth':'500px','overflowX': 'scroll'},
                    row_selectable="single",
                    page_action="native",
                    page_current=0,
                    page_size=50,
                ),

                dbc.Button([clear_icon, "Remove all"], id='button_clear_table_2',
                           color="secondary", className="me-1", n_clicks=0,
                           style={'margin': '30px', 'fontSize': 16, 'font-family': 'sans-serif', }),

                html.Div(id='clear_table_click_2'),
                html.Br(),

                html.Div(id='modify_render')
            ], style={'margin': '50px'})


@app.callback(
    Output('modify_render', 'children'),
    Input('datatable-modify', 'selected_rows'),
)
def clicks(datatable_modify):
    df_ = csv_to_df_data('save_sup.csv', session['session_user'])

    if datatable_modify == None:
        return html.Label([warning_icon, 'Select to modify'],
                          style={'font-family': 'sans-serif', 'fontSize': 22, 'color': 'red',
                                 'width': '500px', 'display': 'inline-block', 'verticalAlign': 'middle',
                                 'margin': '50px'  # 'height':'40px'
                                 }),
    else:
        selection_name = df_.loc[datatable_modify, 'Supplier Name'].iloc[0]
        selection_amount = df_.loc[datatable_modify, 'amount'].iloc[0]
        selection_scf = df_.loc[datatable_modify, 'scf'].iloc[0]
        selection_VMI = df_.loc[datatable_modify, 'VMI'].iloc[0]
        selection_inventory = df_.loc[datatable_modify, 'inventory'].iloc[0]
        selection_overdue = df_.loc[datatable_modify, 'overdue'].iloc[0]
        selection_pay_term = df_.loc[datatable_modify, 'pay_term'].iloc[0]
        selection_business = df_.loc[datatable_modify, 'business'].iloc[0]
        selection_lead_time = df_.loc[datatable_modify, 'lead_time'].iloc[0]
        selection_critical = df_.loc[datatable_modify, 'critical'].iloc[0]
        selection_id = df_.loc[datatable_modify, 'id'].iloc[0]

        return html.Div(children=[

            html.Br(),
            html.Div(children=[

                html.H3('Edit: ' + selection_name,
                        style={'color': 'black', 'font-family': 'sans-serif', 'width': '500px',
                               'fontSize': 28, 'verticalAlign': 'top', 'margin': '20px 20px 20px 20px',
                               'display': 'inline-block', 'horizontalAlign': 'center'}),

                html.Br(),

                html.H3('Supplier ID: ' + selection_id,
                        style={'color': 'black', 'font-family': 'sans-serif', 'width': '500px',
                               'fontSize': 28, 'verticalAlign': 'top', 'margin': '20px 20px 20px 20px',
                               'display': 'inline-block', 'horizontalAlign': 'center'}),

                html.Br(),

                dbc.Input(id='name_edit', value=selection_name, disabled=True
                          , style={'color': 'black', 'fontSize': 0, 'margin': '0px', 'width': '0px',
                                   'display': 'inline-block', 'horizontalAlign': 'center', 'opacity': '0%'}),
                dbc.Input(id='id_edit', value=selection_id, disabled=True
                          , style={'color': 'black', 'fontSize': 0, 'margin': '0px', 'width': '0px',
                                   'display': 'inline-block', 'horizontalAlign': 'center', 'opacity': '0%'}),

                html.Br(),  # ---------AMOUNT

                html.Div(children=[
                    html.H3('Does supplier have SCF now via banks?',
                            style={'color': 'black', 'font-family': 'sans-serif',
                                   'fontSize': body_size, 'verticalAlign': 'top',
                                   'margin': '10px',
                                   'align-items': 'center', 'flex': 1,
                                   'display': 'flex', 'justify-content': 'right'}),

                    dbc.Input(id="amount_edit", placeholder="Amount in $M", type='number', min=0,
                              value=selection_amount,
                              style={'color': 'blue', 'width': '20%', 'font-family': 'sans-serif',
                                     'fontSize': body_size, 'margin': '10px', 'width': '250px',
                                     'align-items': 'center', 'flex': 1,
                                     'display': 'flex', 'justify-content': 'left'}
                              ),

                ], style={'border': 'px solid orange', 'background-color': '#f2f2f2', 'display': 'flex',
                          'border-radius': 20, 'margin': '5px 20px 5px 20px', 'flex': 'row',
                          'horizontalAlign': 'center'}, ),

                html.Br(),  # ---------SCF

                html.Div(children=[
                    html.H3('Does supplier have SCF now via banks?',
                            style={'color': 'black', 'font-family': 'sans-serif',
                                   'fontSize': body_size, 'verticalAlign': 'top',
                                   'margin': '10px',
                                   'align-items': 'center', 'flex': 1,
                                   'display': 'flex', 'justify-content': 'right'}),

                    dcc.Dropdown(id='scf_edit', value=selection_scf, options={'Yes': 'Yes', 'No': 'No'},
                                 searchable=False
                                 , style={'color': 'black', 'font-family': 'sans-serif',
                                          'fontSize': body_size, 'margin': '10px', 'width': '250px',
                                          'align-items': 'center', 'flex': 1,
                                          'display': 'flex', 'justify-content': 'left'}),

                ], style={'border': 'px solid orange', 'background-color': '#f2f2f2', 'display': 'flex',
                          'border-radius': 20, 'margin': '5px 20px 5px 20px', 'flex': 'row',
                          'horizontalAlign': 'center'}, ),

                html.Br(),  # ---------VMI

                html.Div(children=[
                    html.H3('Does Supplier currently have VMI agreement with Customer?',
                            style={'color': 'black', 'font-family': 'sans-serif',
                                   'fontSize': body_size, 'verticalAlign': 'top',
                                   'margin': '10px',
                                   'align-items': 'center', 'flex': 1,
                                   'display': 'flex', 'justify-content': 'right'}),

                    dcc.Dropdown(id='VMI_edit', value=selection_VMI, options={'Yes': 'Yes', 'No': 'No'},
                                 searchable=False
                                 , style={'color': 'black', 'font-family': 'sans-serif',
                                          'fontSize': body_size, 'margin': '10px', 'width': '250px',
                                          'align-items': 'center', 'flex': 1,
                                          'display': 'flex', 'justify-content': 'left'}),

                ], style={'border': 'px solid orange', 'background-color': '#f2f2f2', 'display': 'flex',
                          'border-radius': 20, 'margin': '5px 20px 5px 20px', 'flex': 'row',
                          'horizontalAlign': 'center'}, ),

                html.Br(),  # ---------Critical

                html.Div(children=[
                    html.H3('Is Supplier  a critical supplier  in Client view?',
                            style={'color': 'black', 'font-family': 'sans-serif',
                                   'fontSize': body_size, 'verticalAlign': 'top',
                                   'margin': '10px',
                                   'align-items': 'center', 'flex': 1,
                                   'display': 'flex', 'justify-content': 'right'}),

                    dcc.Dropdown(id='critical_edit', value=selection_critical, options={'Yes': 'Yes', 'No': 'No'},
                                 searchable=False
                                 , style={'color': 'black', 'font-family': 'sans-serif',
                                          'fontSize': body_size, 'margin': '10px', 'width': '250px',
                                          'align-items': 'center', 'flex': 1,
                                          'display': 'flex', 'justify-content': 'left'}),

                ], style={'border': 'px solid orange', 'background-color': '#f2f2f2', 'display': 'flex',
                          'border-radius': 20, 'margin': '5px 20px 5px 20px', 'flex': 'row',
                          'horizontalAlign': 'center'}, ),

                html.Br(),  # ---------inventory

                html.Div(children=[
                    html.H3('Is Supplier inventory  greater than  20% of Client  total inventory?',
                            style={'color': 'black', 'font-family': 'sans-serif',
                                   'fontSize': body_size, 'verticalAlign': 'top',
                                   'margin': '10px',
                                   'align-items': 'center', 'flex': 1,
                                   'display': 'flex', 'justify-content': 'right'}),

                    dcc.Dropdown(id='inventory_edit', value=selection_inventory, options={'Yes': 'Yes', 'No': 'No'},
                                 searchable=False
                                 , style={'color': 'black', 'font-family': 'sans-serif',
                                          'fontSize': body_size, 'margin': '10px', 'width': '250px',
                                          'align-items': 'center', 'flex': 1,
                                          'display': 'flex', 'justify-content': 'left'}),

                ], style={'border': 'px solid orange', 'background-color': '#f2f2f2', 'display': 'flex',
                          'border-radius': 20, 'margin': '5px 20px 5px 20px', 'flex': 'row',
                          'horizontalAlign': 'center'}, ),

                html.Br(),  # -----------------------------------------------pay_term

                html.Div(children=[
                    html.H3('Is payment terms to supplier 45 days or less?',
                            style={'color': 'black', 'font-family': 'sans-serif',
                                   'fontSize': body_size, 'verticalAlign': 'top',
                                   'margin': '10px',
                                   'align-items': 'center', 'flex': 1,
                                   'display': 'flex', 'justify-content': 'right'}),

                    dcc.Dropdown(id='pay_term_edit', value=selection_pay_term, options={'Yes': 'Yes', 'No': 'No'},
                                 searchable=False
                                 , style={'color': 'black', 'font-family': 'sans-serif',
                                          'fontSize': body_size, 'margin': '10px', 'width': '250px',
                                          'align-items': 'center', 'flex': 1,
                                          'display': 'flex', 'justify-content': 'left'}),

                ], style={'border': 'px solid orange', 'background-color': '#f2f2f2', 'display': 'flex',
                          'border-radius': 20, 'margin': '5px 20px 5px 20px', 'flex': 'row',
                          'horizontalAlign': 'center'}, ),

                html.Br(),  # -----------------------------------------------lead_time

                html.Div(children=[
                    html.H3('Is Supplier Lead time  > 90 days?', style={'color': 'black', 'font-family': 'sans-serif',
                                                                        'fontSize': body_size, 'verticalAlign': 'top',
                                                                        'margin': '10px',
                                                                        'align-items': 'center', 'flex': 1,
                                                                        'display': 'flex', 'justify-content': 'right'}),

                    dcc.Dropdown(id='lead_time_edit', value=selection_lead_time, options={'Yes': 'Yes', 'No': 'No'},
                                 searchable=False
                                 , style={'color': 'black', 'font-family': 'sans-serif',
                                          'fontSize': body_size, 'margin': '10px', 'width': '250px',
                                          'align-items': 'center', 'flex': 1,
                                          'display': 'flex', 'justify-content': 'left'}),

                ], style={'border': 'px solid orange', 'background-color': '#f2f2f2', 'display': 'flex',
                          'border-radius': 20, 'margin': '5px 20px 5px 20px', 'flex': 'row',
                          'horizontalAlign': 'center'}, ),

                html.Br(),  # -----------------------------------------------business

                html.Div(children=[
                    html.H3('Is Client business  greater than  20%  of Supplier total business?',
                            style={'color': 'black', 'font-family': 'sans-serif',
                                   'fontSize': body_size, 'verticalAlign': 'top',
                                   'margin': '10px',
                                   'align-items': 'center', 'flex': 1,
                                   'display': 'flex', 'justify-content': 'right'}),

                    dcc.Dropdown(id='business_edit', value=selection_business, options={'Yes': 'Yes', 'No': 'No'},
                                 searchable=False
                                 , style={'color': 'black', 'font-family': 'sans-serif',
                                          'fontSize': body_size, 'margin': '10px', 'width': '250px',
                                          'align-items': 'center', 'flex': 1,
                                          'display': 'flex', 'justify-content': 'left'}),

                ], style={'border': 'px solid orange', 'background-color': '#f2f2f2', 'display': 'flex',
                          'border-radius': 20, 'margin': '5px 20px 5px 20px', 'flex': 'row',
                          'horizontalAlign': 'center'}, ),

                html.Br(),  # -----------------------------------------------overdue

                html.Div(children=[
                    html.H3('Are supplier Invoices overdue by 30 days or greater?',
                            style={'color': 'black', 'font-family': 'sans-serif',
                                   'fontSize': body_size, 'verticalAlign': 'top',
                                   'margin': '10px',
                                   'align-items': 'center', 'flex': 1,
                                   'display': 'flex', 'justify-content': 'right'}),

                    dcc.Dropdown(id='overdue_edit', value=selection_overdue, options={'Yes': 'Yes', 'No': 'No'},
                                 searchable=False
                                 , style={'color': 'black', 'font-family': 'sans-serif',
                                          'fontSize': body_size, 'margin': '10px', 'width': '250px',
                                          'align-items': 'center', 'flex': 1,
                                          'display': 'flex', 'justify-content': 'left'}),

                ], style={'border': 'px solid orange', 'background-color': '#f2f2f2', 'display': 'flex',
                          'border-radius': 20, 'margin': '5px 20px 5px 20px', 'flex': 'row',
                          'horizontalAlign': 'center'}, ),

                html.Br(),

                dbc.Button([edit_icon, "Save"], id='button_edit_sup', color="primary", className="me-1", n_clicks=0,
                           style={'margin': '20px 20px 20px 20px'}),
                dbc.Button([clear_icon, "Remove Supplier"], id='button_del_sup', color="secondary", className="me-1",
                           n_clicks=0,
                           style={'margin': '20px 20px 20px 20px'}),
                html.Div(id='button-clicks-edit'),
                html.Div(id='button-clicks-del'),

            ], style={'width': '95%', 'border': 'px solid orange', 'box-shadow': '5px 5px 15px 8px lightgrey',
                      'background-color': 'white', 'display': 'inline-block',
                      'border-radius': 20, 'margin': '50px', 'padding': '50px'},

            )
        ])


@app.callback(
    Output('supplier_score', 'children'),
    Input('name', 'value'),
    Input('amount', 'value'),
    Input('scf', 'value'),
    Input('VMI', 'value'),
    Input('critical', 'value'),
    Input('inventory', 'value'),
    Input('pay_term', 'value'),
    Input('lead_time', 'value'),
    Input('business', 'value'),
    Input('overdue', 'value')
)
def sup_score(name_,
              amount_,
              scf_,
              VMI_,
              critical_,
              inventory_,
              pay_term_,
              lead_time_,
              business_,
              overdue_, ):
    # process score:
    score = weighted_total(name_,
                           amount_,
                           scf_,
                           VMI_,
                           critical_,
                           inventory_,
                           pay_term_,
                           lead_time_,
                           business_,
                           overdue_, )
    color = generate_color_code(score)

    nb_sup = test_length('save_sup.csv')
    if nb_sup == False:
        return html.Div(children=[html.Div(children=[
            html.Label([warning_icon,
                        'You reached the maximum of 10 suppliers in the ranking -- Clear the table or remove some to rank other ones'],
                       style={'font-family': 'sans-serif', 'fontSize': 22, 'color': 'red',
                              'width': '80%', 'display': 'inline-block', 'verticalAlign': 'middle',
                              'margin': '15px 15px 15px 15px'  # 'height':'40px'
                              })
        ], style={'border': '0px solid orange', 'background-color': '#ffebeb', 'display': 'inline-block',
                  'border-radius': 20, 'horizontalAlign': 'center', 'margin': '15px 15px 15px 15px'}), ])

    else:

        if score < 0:
            return html.Div(children=[html.Div(children=[
                html.Label([warning_icon, 'Please answer all the fields'],
                           style={'font-family': 'sans-serif', 'fontSize': 22, 'color': 'red',
                                  'width': '500px', 'display': 'inline-block', 'verticalAlign': 'middle',
                                  'margin': '15px 15px 15px 15px'  # 'height':'40px'
                                  }),
            ], style={'border': '0px solid orange', 'background-color': '#ffebeb', 'display': 'inline-block',
                      'border-radius': 20, 'horizontalAlign': 'center', 'margin': '15px 15px 15px 15px'}), ])
        else:
            if check_duplicate(name_) == True:
                return html.Div(children=[html.Div(children=[
                    html.Label([warning_icon, 'This supplier already exist in the ranking'],
                               style={'font-family': 'sans-serif', 'fontSize': 22, 'color': 'orange',
                                      'width': '500px', 'display': 'inline-block', 'verticalAlign': 'middle',
                                      'margin': '15px 15px 15px 15px'  # 'height':'40px'
                                      }),
                ], style={'border': '0px solid orange', 'background-color': '#ffecd9', 'display': 'inline-block',
                          'border-radius': 20, 'horizontalAlign': 'center', 'margin': '15px 15px 15px 15px'}), ])

            else:
                return html.Div(children=[html.Div(children=[
                    html.Label('Supplier score:', style={'font-family': 'sans-serif', 'fontSize': 20, 'color': 'black',
                                                         'width': '500px', 'display': 'inline-block',
                                                         'verticalAlign': 'middle',  # 'height':'40px'
                                                         }),
                    html.Div(children=[
                        html.Label(str(score) + '/10',
                                   style={'font-family': 'sans-serif', 'fontSize': 20, 'color': 'blue',
                                          'display': 'inline-block', 'verticalAlign': 'middle',  # 'height':'40px'
                                          }),
                        html.Div(children=[html.H3('.', style={'fontSize': 0}), ],
                                 style={'width': '30px', 'height': '30px', 'display': 'inline-block',
                                        'margin': '0px 5px 0px 5px',
                                        'color': 'blue', 'horizontalAlign': 'right', 'verticalAlign': 'middle',
                                        'border': '0px solid orange', 'border-radius': 30,
                                        'font-family': 'sans-serif', 'fontSize': 20, 'background-color': color}),
                    ], style={'margin': '10px 10px 10px 10px'}),

                    # dcc.Location(id='button-clicks', refresh=False),

                    dbc.Button([add_icon, "Save & Rank supplier"], id='button_rank_supplier',
                               color="primary", className="me-1", n_clicks=0,
                               style={'margin': '20px 20px 20px 20px', 'fontSize': 16, 'font-family': 'sans-serif', }),
                    # html.Div(id='button-clicks'),
                    html.Div(id='add_sup_click'),
                ]),
                ], style={'border': '0px solid orange', 'background-color': '#dff7e5', 'display': 'inline-block',
                          'border-radius': 20, 'horizontalAlign': 'center', 'margin': '15px 15px 15px 15px',
                          'padding': '15px 15px 15px 15px'})


@app.callback(
    Output('add_sup_click', 'children'),
    [Input('button_rank_supplier', 'n_clicks'),
     Input('name', 'value'),
     Input('amount', 'value'),
     Input('scf', 'value'),
     Input('VMI', 'value'),
     Input('critical', 'value'),
     Input('inventory', 'value'),
     Input('pay_term', 'value'),
     Input('lead_time', 'value'),
     Input('business', 'value'),
     Input('overdue', 'value')])
def clicks(n_clicks,
           name,
           amount,
           scf_,
           VMI_,
           critical_,
           inventory_,
           pay_term_,
           lead_time_,
           business_,
           overdue_):
    if n_clicks > 0:
        sup = Supplier(name, amount, scf_, VMI_, critical_, inventory_, pay_term_, lead_time_, business_, overdue_)
        sup.add_supplier(session['session_user'])
        sup.save_add_tcc(session['session_user'])
        return html.Div(children=[
            dbc.Button([new_icon, " Add another supplier"], id='button_new_sup',
                       color="info", className="me-1", n_clicks=0,
                       style={'margin': '20px 20px 20px 20px'}),
            dbc.Button([rank_icon, " Go to ranking"], id='button_go-to-ranking',
                       color="info", className="me-1", n_clicks=0,
                       style={'margin': '20px 20px 20px 20px'}),

        ])


@app.callback(
    Output('tabs_common_summary', 'value'),
    [
        Input('button_new_sup', 'n_clicks'),
        Input('button_go-to-ranking', 'n_clicks')
    ]
)
def update_tabs_common_summary(btn_new_sup_clicks, btn_go_to_ranking_clicks):  # return nothing
    if btn_new_sup_clicks is not None and btn_new_sup_clicks > 0:
        return 'tab_1'

    if btn_go_to_ranking_clicks is not None and btn_go_to_ranking_clicks > 0:
        return 'tab_3'

    else:
        return dash.no_update


@app.callback(
    Output('supplier_table', 'children'),
    Input('tabs_common_summary', 'value'),
)
def sup_score(tab):
    df_sup = csv_to_df_2('save_sup.csv', session["session_user"])
    user_ = session['session_user']
    if df_sup.shape[1] == 1:
        return html.H3('No supplier is currently ranked, go to -- Criteria responses tab and enter responses',
                       style={'color': '#383838', 'font-family': 'sans-serif',
                              'fontSize': 22, 'verticalAlign': 'top', 'margin': '50px',
                              'display': 'inline-block', 'horizontalAlign': 'center',
                              'border': '0px solid orange', 'background-color': 'white', 'display': 'inline-block',
                              'border-radius': 20, 'horizontalAlign': 'center', 'padding': '50px'}),
    else:
        return html.Div([
            html.H3('Supplier Ranking', style={'color': 'black', 'font-family': 'sans-serif', 'width': '300px',
                                               'fontSize': title_size, 'verticalAlign': 'top',
                                               'margin': '0px 50px 50px 50px',
                                               'display': 'inline-block', 'horizontalAlign': 'center'}),

            html.Br(),
            DataTable(
                id='datatable_1',
                columns=[
                    {"name": str(i), "id": str(i), "deletable": True, "selectable": True} for i in df_sup.columns
                ],
                data=df_sup.reset_index().to_dict('records'),

                sort_action="native",
                sort_mode="multi",
                style_header={
                    'backgroundColor': 'rgb(117, 125, 120)',
                    'fontWeight': 'bold',
                    'color': 'white'
                },
                style_data_conditional=[
                    {
                        'if': {
                            'filter_query': '{Supplier} contains "Responses"'
                        },
                        'backgroundColor': 'rgb(117, 125, 120)',
                        'fontWeight': 'bold',
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{Supplier} contains "Rank"'
                        },
                        'backgroundColor': '#c7c7c7',
                        'color': 'black'
                    },
                    {
                        'if': {
                            'filter_query': '{Supplier} contains "Rating (out of 10)"'
                        },
                        'backgroundColor': '#c7c7c7',
                        'color': 'black'
                    }
                ],
                style_cell={'padding': '10px', 'font-family': 'sans-serif', 'fontSize': 24},
                style_table={'maxWidth': '100%', 'overflowX': 'scroll'},
                selected_columns=[],
                selected_rows=[],
                page_action="native",
                page_current=0,
                page_size=50,
            ),

            html.Br(),
            dcc.Graph(
                id='rank-graph',
                figure=quadrant(user_)
            ),

            html.Br(),
            # html.A(, id='download-link', download="ranking_supplier_TCC.csv", href="", target="_blank"),
            html.A([dl_icon, 'Download ranking'], id='download-link', download="ranking_supplier_TCC.xlsx", href="",
                   target="_blank"),
            # html.Br(),
            dbc.Button([clear_icon, "Clear ranking"], id='button_clear_table',
                       color="secondary", className="me-1", n_clicks=0,
                       style={'margin': '20px 20px 20px 20px', 'fontSize': 16, 'font-family': 'sans-serif', }),

            html.Div(id='clear_table_click'),

        ], style={'border': 'px solid orange', 'background-color': 'white',
                  'display': 'inline-block', 'width': '95%', 'box-shadow': '5px 5px 15px 8px lightgrey',
                  'border-radius': 20, 'margin': '50px', 'horizontalAlign': 'center', 'padding': '50px'}),


@app.callback(
    Output('supplier_table_2', 'children'),
    [Input('scf_wt', 'value'),
     Input('VMI_wt', 'value'),
     Input('critical_wt', 'value'),
     Input('inventory_wt', 'value'),
     Input('pay_term_wt', 'value'),
     Input('lead_time_wt', 'value'),
     Input('business_wt', 'value'),
     Input('overdue_wt', 'value')],
)
def sup_score_2(scf_wt,
                VMI_wt,
                critical_wt,
                inventory_wt,
                pay_term_wt,
                lead_time_wt,
                business_wt,
                overdue_wt):
    df_sup = csv_to_df_live('save_sup.csv',
                            scf_wt,
                            VMI_wt,
                            critical_wt,
                            inventory_wt,
                            pay_term_wt,
                            lead_time_wt,
                            business_wt,
                            overdue_wt)

    if df_sup.empty:
        pass
    else:
        return html.Div([
            html.H3('Supplier Ranking', style={'color': 'black', 'font-family': 'sans-serif', 'width': '300px',
                                               'fontSize': title_size, 'verticalAlign': 'top', 'margin': '50px',
                                               'display': 'inline-block', 'horizontalAlign': 'center'}),

            html.Br(),
            DataTable(
                id='datatable_2',
                columns=[
                    {"name": i, "id": i, "deletable": True, "selectable": True} for i in df_sup.columns
                ],
                data=df_sup.to_dict('records'),
                # editable=True,
                # filter_action="disable",
                sort_action="native",
                sort_mode="multi",
                # column_selectable="single",
                # row_selectable="single",
                # row_deletable=True,
                style_cell={'padding': '10px', 'font-family': 'sans-serif', 'fontSize': 24},
                selected_columns=[],
                selected_rows=[],
                page_action="native",
                page_current=0,
                page_size=50,
            ),

        ], style={'margin': '50px'}),


@app.callback(Output('clear_table_click', 'children'), [Input('button_clear_table', 'n_clicks')])
def clicks(n_clicks):
    user_ = session['session_user']
    if n_clicks > 0:
        clear_suppliers(user_)
        return html.H3([ok_icon, 'Ranking cleared -- RELOAD the page'],
                       style={'color': 'grey', 'font-family': 'sans-serif',
                              'fontSize': 18, 'verticalAlign': 'top', 'margin': '10px',
                              'display': 'inline-block', 'horizontalAlign': 'center'})


@app.callback(Output('clear_table_click_2', 'children'), [Input('button_clear_table_2', 'n_clicks')])
def clicks(n_clicks):
    user_ = session['session_user']
    if n_clicks > 0:
        clear_suppliers(user_)
        return html.H3([ok_icon, 'Ranking cleared -- RELOAD the page'],
                       style={'color': 'grey', 'font-family': 'sans-serif',
                              'fontSize': 18, 'verticalAlign': 'top', 'margin': '10px',
                              'display': 'inline-block', 'horizontalAlign': 'center'}),


@app.callback(Output('change_param', 'children'), [Input('tabs_common_summary', 'value')])
def clicks(tab):
    df = pd.read_csv('param_wt.csv', header=0)
    return html.Div(children=[

        html.Div(children=[

            html.H3('Edit criteria weightage (Total must be equal to 100):',
                    style={'color': 'black', 'font-family': 'sans-serif',
                           'fontSize': title_size, 'verticalAlign': 'top', 'width': '100%',
                           'margin': '22px',
                           'align-items': 'center', 'flex': 1,
                           'display': 'flex', 'justify-content': 'center'}),

            html.Div(children=[

                html.H3('Criteria 1 (Supplier has access to SCF programs) %:',
                        style={'color': 'black', 'font-family': 'sans-serif',
                               'fontSize': 18, 'verticalAlign': 'top', 'width': '40%',
                               'margin': '10px',
                               'align-items': 'center', 'flex': 1,
                               'display': 'flex', 'justify-content': 'right'}),

                dbc.Input(id="scf_wt", type='number', min=0, max=100, value=df['scf'][0] * 100, step=1,
                          style={'color': 'black', 'font-family': 'sans-serif',
                                 'fontSize': 18, 'verticalAlign': 'top', 'width': '40%',
                                 'margin': '10px',
                                 'align-items': 'center', 'flex': 1,
                                 'display': 'flex', 'justify-content': 'right'}),
            ], style={'display': 'flex', 'margin': '12px', 'flex': 'row', 'horizontalAlign': 'center'}),

            html.Div(children=[

                html.H3('Criteria 2 (Supplier offers VMI to clients) %:',
                        style={'color': 'black', 'font-family': 'sans-serif',
                               'fontSize': 18, 'verticalAlign': 'top', 'width': '40%',
                               'margin': '10px',
                               'align-items': 'center', 'flex': 1,
                               'display': 'flex', 'justify-content': 'right'}),

                dbc.Input(id="VMI_wt", type='number', min=0, max=100, value=df['VMI'][0] * 100, step=1,
                          style={'color': 'black', 'font-family': 'sans-serif',
                                 'fontSize': 18, 'verticalAlign': 'top', 'width': '40%',
                                 'margin': '10px',
                                 'align-items': 'center', 'flex': 1,
                                 'display': 'flex', 'justify-content': 'right'}),
            ], style={'display': 'flex', 'margin': '12px', 'flex': 'row', 'horizontalAlign': 'center'}),

            html.Div(children=[

                html.H3("Criteria 3 (Supplier is a critical for client) %:",
                        style={'color': 'black', 'font-family': 'sans-serif',
                               'fontSize': 18, 'verticalAlign': 'top', 'width': '40%',
                               'margin': '10px',
                               'align-items': 'center', 'flex': 1,
                               'display': 'flex', 'justify-content': 'right'}),

                dbc.Input(id="critical_wt", type='number', min=0, max=100, value=df['critical'][0] * 100, step=1,
                          style={'color': 'black', 'font-family': 'sans-serif',
                                 'fontSize': 18, 'verticalAlign': 'top', 'width': '20px',
                                 'margin': '10px',
                                 'align-items': 'center', 'flex': 1,
                                 'display': 'flex', 'justify-content': 'right'}),
            ], style={'display': 'flex', 'margin': '12px', 'flex': 'row', 'horizontalAlign': 'center'}),

            html.Div(children=[

                html.H3("Criteria 4 (Supplier inventory is 20%+ for client ) %:",
                        style={'color': 'black', 'font-family': 'sans-serif',
                               'fontSize': 18, 'verticalAlign': 'top', 'width': '40%',
                               'margin': '10px',
                               'align-items': 'center', 'flex': 1,
                               'display': 'flex', 'justify-content': 'right'}),

                dbc.Input(id="inventory_wt", type='number', min=0, max=100, value=df['inventory'][0] * 100, step=1,
                          style={'color': 'black', 'font-family': 'sans-serif',
                                 'fontSize': 18, 'verticalAlign': 'top', 'width': '40%',
                                 'margin': '10px',
                                 'align-items': 'center', 'flex': 1,
                                 'display': 'flex', 'justify-content': 'right'}),
            ], style={'display': 'flex', 'margin': '12px', 'flex': 'row', 'horizontalAlign': 'center'}),

            html.Div(children=[

                html.H3('Criteria 5 (Payment terms are below 45 days) %:',
                        style={'color': 'black', 'font-family': 'sans-serif',
                               'fontSize': 18, 'verticalAlign': 'top', 'width': '40%',
                               'margin': '10px',
                               'align-items': 'center', 'flex': 1,
                               'display': 'flex', 'justify-content': 'right'}),

                dbc.Input(id="pay_term_wt", type='number', min=0, max=100, value=df['pay_term'][0] * 100, step=1,
                          style={'color': 'black', 'font-family': 'sans-serif',
                                 'fontSize': 18, 'verticalAlign': 'top', 'width': '40%',
                                 'margin': '10px',
                                 'align-items': 'center', 'flex': 1,
                                 'display': 'flex', 'justify-content': 'right'}),
            ], style={'display': 'flex', 'margin': '12px', 'flex': 'row', 'horizontalAlign': 'center'}),

            html.Div(children=[

                html.H3("Criteria 6 (Lead times are 90+ days) %:", style={'color': 'black', 'font-family': 'sans-serif',
                                                                          'fontSize': 18, 'verticalAlign': 'top',
                                                                          'width': '40%',
                                                                          'margin': '10px',
                                                                          'align-items': 'center', 'flex': 1,
                                                                          'display': 'flex',
                                                                          'justify-content': 'right'}),

                dbc.Input(id="lead_time_wt", type='number', min=0, max=100, value=df['lead_time'][0] * 100, step=1,
                          style={'color': 'black', 'font-family': 'sans-serif',
                                 'fontSize': 18, 'verticalAlign': 'top', 'width': '40%',
                                 'margin': '10px',
                                 'align-items': 'center', 'flex': 1,
                                 'display': 'flex', 'justify-content': 'right'}),
            ], style={'display': 'flex', 'margin': '12px', 'flex': 'row', 'horizontalAlign': 'center'}),

            html.Div(children=[

                html.H3("Criteria 7 (Client business is 20%+ of supplier business) %:",
                        style={'color': 'black', 'font-family': 'sans-serif',
                               'fontSize': 18, 'verticalAlign': 'top', 'width': '40%',
                               'margin': '10px',
                               'align-items': 'center', 'flex': 1,
                               'display': 'flex', 'justify-content': 'right'}),

                dbc.Input(id="business_wt", type='number', min=0, max=100, value=df['business'][0] * 100, step=1,
                          style={'color': 'black', 'font-family': 'sans-serif',
                                 'fontSize': 18, 'verticalAlign': 'top', 'width': '20px',
                                 'margin': '10px',
                                 'align-items': 'center', 'flex': 1,
                                 'display': 'flex', 'justify-content': 'right'}),
            ], style={'display': 'flex', 'margin': '12px', 'flex': 'row', 'horizontalAlign': 'center'}),

            html.Div(children=[

                html.H3("Criteria 8 (Supplier Invoices overdue 30+ days) %:",
                        style={'color': 'black', 'font-family': 'sans-serif',
                               'fontSize': 18, 'verticalAlign': 'top', 'width': '40%',
                               'margin': '10px',
                               'align-items': 'center', 'flex': 1,
                               'display': 'flex', 'justify-content': 'right'}),

                dbc.Input(id="overdue_wt", type='number', min=0, max=100, value=df['overdue'][0] * 100, step=1,
                          style={'color': 'black', 'font-family': 'sans-serif',
                                 'fontSize': 18, 'verticalAlign': 'top', 'width': '40%',
                                 'margin': '10px',
                                 'align-items': 'center', 'flex': 1,
                                 'display': 'flex', 'justify-content': 'right'}),
            ], style={'display': 'flex', 'margin': '12px', 'flex': 'row', 'horizontalAlign': 'center'}),

            html.Div(id='wt_engine'),

        ], style={'border': 'px solid orange', 'background-color': 'white', 'width': '75%', 'horizontalAlign': 'center',
                  'border-radius': 20, 'margin': '0px', 'padding': '20px', 'display': 'inline-block'}),

        # html.Div(children=[html.Div(id='supplier_table_2')],style={'width':'30%','display':'inline-block','verticalAlign': 'top',}),

    ], style={'border': 'px solid orange', 'width': '100%', 'display': 'inline-block',
              'border-radius': 20, 'margin': '50px', 'horizontalAlign': 'center'})


@app.callback(
    Output('wt_engine', 'children'),
    [Input('scf_wt', 'value'),
     Input('VMI_wt', 'value'),
     Input('critical_wt', 'value'),
     Input('inventory_wt', 'value'),
     Input('pay_term_wt', 'value'),
     Input('lead_time_wt', 'value'),
     Input('business_wt', 'value'),
     Input('overdue_wt', 'value')])
def wt_engine(scf_wt,
              VMI_wt,
              critical_wt,
              inventory_wt,
              pay_term_wt,
              lead_time_wt,
              business_wt,
              overdue_wt):
    if any([arg is None for arg in [scf_wt,
                                    VMI_wt,
                                    critical_wt,
                                    inventory_wt,
                                    pay_term_wt,
                                    lead_time_wt,
                                    business_wt,
                                    overdue_wt, ]]):
        return html.Label([warning_icon, '/!\ One param is <Null> - Please change it to <0>'],
                          style={'font-family': 'sans-serif', 'fontSize': 22, 'color': 'red',
                                 'width': '500px', 'display': 'inline-block', 'verticalAlign': 'middle',
                                 'margin': '15px 15px 15px 15px'  # 'height':'40px'
                                 }),

    else:

        rslt = scf_wt + VMI_wt + critical_wt + inventory_wt + pay_term_wt + lead_time_wt + business_wt + overdue_wt

        if (rslt / 100) == 1:
            return html.Div(children=[
                dbc.Button([change_icon, "Edit weightage"], id='button_change_param',
                           color="primary", className="me-1", n_clicks=0,
                           style={'margin': '20px 20px 20px 20px', 'fontSize': 16, 'font-family': 'sans-serif', }),
                html.Div(id='change_param_click'),
            ])
        else:
            return html.Label([warning_icon, 'The total should be 100% -- Total is now: ' + str(rslt) + '%'],
                              style={'font-family': 'sans-serif', 'fontSize': 22, 'color': 'red',
                                     'width': '500px', 'display': 'inline-block', 'verticalAlign': 'middle',
                                     'margin': '15px 15px 15px 15px'  # 'height':'40px'
                                     }),


@app.callback(
    Output('change_param_click', 'children'),
    [Input('button_change_param', 'n_clicks'),
     Input('scf_wt', 'value'),
     Input('VMI_wt', 'value'),
     Input('critical_wt', 'value'),
     Input('inventory_wt', 'value'),
     Input('pay_term_wt', 'value'),
     Input('lead_time_wt', 'value'),
     Input('business_wt', 'value'),
     Input('overdue_wt', 'value')])
def clicks_param(n_clicks,
                 scf_wt,
                 VMI_wt,
                 critical_wt,
                 inventory_wt,
                 pay_term_wt,
                 lead_time_wt,
                 business_wt,
                 overdue_wt):
    if n_clicks > 0:
        data = {'scf': [scf_wt / 100],
                'VMI': [VMI_wt / 100],
                'critical': [critical_wt / 100],
                'inventory': [inventory_wt / 100],
                'pay_term': [pay_term_wt / 100],
                'lead_time': [lead_time_wt / 100],
                'business': [business_wt / 100],
                'overdue': [overdue_wt / 100]}

        df = pd.DataFrame(data)

        df.to_csv('param_wt.csv', index=False)
        return html.H3([ok_icon, 'Weightage updated'], style={'color': 'green', 'font-family': 'sans-serif',
                                                              'fontSize': 18, 'verticalAlign': 'top', 'margin': '10px',
                                                              'display': 'inline-block', 'horizontalAlign': 'center'}),


@app.callback(
    Output('button-clicks-del', 'children'),
    [Input('button_del_sup', 'n_clicks'),
     Input('id_edit', 'value'),
     ])
def clicks(n_clicks, id_):
    if n_clicks > 0:
        del_sup(id_)
        return html.H3([ok_icon, 'Supplier removed from the list /!\ reload the page to update'],
                       style={'color': 'green', 'font-family': 'sans-serif',
                              'fontSize': 18, 'verticalAlign': 'top', 'margin': '10px',
                              'display': 'inline-block', 'horizontalAlign': 'center'}),


@app.callback(Output('download-link', 'href'),
              Input('download-link', 'n_clicks'))
def download_xlsx(n_clicks):
    df = csv_to_df_2('save_sup.csv', session["session_user"])

    xlsx_data = DL_ranking(df)
    b64_data = base64.b64encode(xlsx_data).decode('utf-8')
    href_data = f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=utf-8;base64,{b64_data}"
    return href_data


@app.callback(
    Output('button-clicks-edit', 'children'),
    [Input('button_edit_sup', 'n_clicks'),
     Input('name_edit', 'value'),
     Input('id_edit', 'value'),
     Input('amount_edit', 'value'),
     Input('scf_edit', 'value'),
     Input('VMI_edit', 'value'),
     Input('critical_edit', 'value'),
     Input('inventory_edit', 'value'),
     Input('pay_term_edit', 'value'),
     Input('lead_time_edit', 'value'),
     Input('business_edit', 'value'),
     Input('overdue_edit', 'value')])
def clicks_edit_sup(n_clicks, name, id_, amount_, scf_, VMI_, critical_, inventory_, pay_term_, lead_time_, business_,
                    overdue_):
    user_ = session['session_user']
    if n_clicks > 0:
        if any([arg is None for arg in [name,
                                        amount_,
                                        scf_,
                                        VMI_,
                                        critical_,
                                        inventory_,
                                        pay_term_,
                                        lead_time_,
                                        business_,
                                        overdue_, ]]) or name == '':

            return html.H3([warning_icon, 'Please provide an answer for all criterias'],
                           style={'color': 'red', 'font-family': 'sans-serif',
                                  'fontSize': 18, 'verticalAlign': 'top', 'margin': '10px',
                                  'display': 'inline-block', 'horizontalAlign': 'center'}),
        else:
            edit_sup(user_, name, amount_, scf_, VMI_, critical_, inventory_, pay_term_, lead_time_, business_,
                     overdue_, id_)
            return html.H3([ok_icon, 'Edited /!\ reload the page to update'],
                           style={'color': 'green', 'font-family': 'sans-serif',
                                  'fontSize': 18, 'verticalAlign': 'top', 'margin': '10px',
                                  'display': 'inline-block', 'horizontalAlign': 'center'}),


if __name__ == "__main__":
    app.run_server(port=8000, debug=True, use_reloader=False)
