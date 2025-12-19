import dash
from dash import dcc, html, Input, Output, State, callback_context
import pandas as pd
import plotly.graph_objects as go
import os
import math

# ==========================================
# CONFIGURATION
# ==========================================
INPUT_FILE = 'mt5_data.csv'       # Your original MT5 export
OUTPUT_FILE = 'labeled_data.csv'  # Where labels are saved
PAGE_SIZE = 200                   # Number of candles per page
# ==========================================

# 1. LOAD DATA FUNCTION (Same robust logic as before)
# ... inside labeler_v2.py ...

def load_data():
    if os.path.exists(OUTPUT_FILE):
        print(f"🔄 Loading existing progress from {OUTPUT_FILE}...")
        df = pd.read_csv(OUTPUT_FILE)
        
        # OPTIMIZATION 1: Fast Date Parsing for the saved file
        # The saved file is standard ISO format (YYYY-MM-DD HH:MM:SS)
        df['time'] = pd.to_datetime(df['time'], format='ISO8601')
        
    elif os.path.exists(INPUT_FILE):
        print(f"📂 Loading fresh data from {INPUT_FILE}...")
        try:
            # OPTIMIZATION 2: Read only needed columns first to save memory
            df = pd.read_csv(INPUT_FILE, sep='\t', engine='python')
            
            # Clean columns
            df.columns = df.columns.str.replace('<', '').str.replace('>', '').str.strip()
            
            # OPTIMIZATION 3: Fast Merge & Parse
            # We combine strings first, then convert with a specific format
            # MT5 format is usually: 2023.09.01 00:00:00
            time_strings = df['DATE'].astype(str) + ' ' + df['TIME'].astype(str)
            df['time'] = pd.to_datetime(time_strings, format='%Y.%m.%d %H:%M:%S')
            
            df.rename(columns={'OPEN': 'open', 'HIGH': 'high', 'LOW': 'low', 'CLOSE': 'close'}, inplace=True)
            df = df[['time', 'open', 'high', 'low', 'close']]
            df['label_breakout'] = False 
        except Exception as e:
            print(f"❌ Error parsing CSV: {e}")
            quit()
    else:
        print("❌ No data file found.")
        quit()
    
    # Sort and reset
    df = df.sort_values('time').reset_index(drop=True)
    print(f"✅ Loaded {len(df)} candles!")
    return df

# Load initial data
df_initial = load_data()

app = dash.Dash(__name__)

# 2. LAYOUT
app.layout = html.Div([
    html.H3("MT5 Data Labeler (Paged)", style={'textAlign': 'center'}),
    
    # CONTROL PANEL (Pagination + Save)
    html.Div([
        # Existing buttons...
        html.Button('Previous', id='btn-prev', n_clicks=0, style={'marginRight': '10px'}),
        html.Span(id='page-info', style={'fontWeight': 'bold', 'margin': '0 10px'}),
        html.Button('Next', id='btn-next', n_clicks=0, style={'marginLeft': '10px', 'marginRight': '30px'}),
        
        # --- NEW: JUMP TO PAGE ---
        html.Span("Go to:", style={'marginLeft': '20px'}),
        dcc.Input(id='input-page-jump', type='number', min=1, step=1, style={'width': '50px', 'marginLeft': '5px'}),
        html.Button('Go', id='btn-go', n_clicks=0, style={'marginLeft': '5px', 'marginRight': '30px'}),
        # -------------------------

        html.Button('Save to CSV', id='btn-save', n_clicks=0, 
                   style={'backgroundColor': 'green', 'color': 'white'}),
        html.Span(id='save-status', style={'marginLeft': '10px', 'color': 'green'})
    ], style={'textAlign': 'center', 'marginBottom': '10px'}),

    # CHART
    dcc.Graph(id='candle-chart', style={'height': '80vh'}),
    
    # STORES (Memory)
    # 1. The Full Dataset
    dcc.Store(id='store-data', data=df_initial.to_dict('records')),
    # 2. The Current Page Number (starts at 0)
    dcc.Store(id='store-page', data=0)
])

# 3. MAIN CALLBACK
@app.callback(
    [Output('candle-chart', 'figure'),
     Output('store-data', 'data'),
     Output('store-page', 'data'),
     Output('page-info', 'children'),
     Output('save-status', 'children'),
     Output('input-page-jump', 'value')], # Update input box to show current page
    
    [Input('btn-prev', 'n_clicks'),
     Input('btn-next', 'n_clicks'),
     Input('btn-go', 'n_clicks'),        # <--- NEW INPUT
     Input('btn-save', 'n_clicks'),
     Input('candle-chart', 'clickData')],
    
    [State('store-data', 'data'),
     State('store-page', 'data'),
     State('input-page-jump', 'value')]  # <--- NEW STATE
)
def update_all(btn_prev, btn_next, btn_go, btn_save, clickData, 
               current_data, current_page, jump_value):
    
    ctx = callback_context
    if not ctx.triggered:
        trigger_id = 'No Trigger'
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Convert dictionary back to DataFrame
    df = pd.DataFrame(current_data)
    # SAFETY: Ensure time is datetime
    df['time'] = pd.to_datetime(df['time'])
    
    total_pages = math.ceil(len(df) / PAGE_SIZE)
    msg = ""

    # --- HANDLE PAGINATION & JUMP ---
    if trigger_id == 'btn-prev':
        current_page = max(0, current_page - 1)
    elif trigger_id == 'btn-next':
        current_page = min(total_pages - 1, current_page + 1)
    elif trigger_id == 'btn-go' and jump_value is not None:
        # Convert 1-based user input to 0-based index
        target_page = int(jump_value) - 1
        # Ensure it stays within valid bounds
        if 0 <= target_page < total_pages:
            current_page = target_page

    # --- HANDLE SAVE ---
    if trigger_id == 'btn-save':
        df.to_csv(OUTPUT_FILE, index=False)
        msg = "Saved!"

    # --- HANDLE LABELING (CLICK) ---
    if trigger_id == 'candle-chart' and clickData:
        clicked_x = clickData['points'][0]['x']
        mask = df['time'] == clicked_x
        if mask.any():
            val = df.loc[mask, 'label_breakout'].values[0]
            df.loc[mask, 'label_breakout'] = not val

    # --- SLICE DATA ---
    start_idx = current_page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    df_page = df.iloc[start_idx:end_idx].copy()

    # --- DRAW CHART ---
    fig = go.Figure(data=[go.Candlestick(
        x=df_page['time'],
        open=df_page['open'], high=df_page['high'],
        low=df_page['low'], close=df_page['close'],
        name='OHLC'
    )])

    labeled_page = df_page[df_page['label_breakout'] == True]
    if not labeled_page.empty:
        fig.add_trace(go.Scatter(
            x=labeled_page['time'], 
            y=labeled_page['high'], 
            mode='markers',
            marker=dict(symbol='triangle-down', size=15, color='blue'),
            name='Breakout'
        ))

    # Dynamic UI Revision (resets zoom only when page changes)
    fig.update_layout(
        uirevision=f'page-{current_page}', 
        title=f'Page {current_page + 1} of {total_pages}',
        xaxis_rangeslider_visible=False,
        dragmode='pan',
        margin=dict(l=40, r=40, t=40, b=40)
    )

    page_info_text = f"Page {current_page + 1} / {total_pages}"

    # Return everything (Current Page + 1 goes back to the input box)
    return fig, df.to_dict('records'), current_page, page_info_text, msg, (current_page + 1)

if __name__ == '__main__':
    app.run(debug=True)