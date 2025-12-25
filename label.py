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
PAGE_SIZE = 200                   # Candles per page
# ==========================================

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

app = dash.Dash(__name__)

# ==========================================
# DYNAMIC LAYOUT (Fixes the Reload Issue)
# ==========================================
def serve_layout():
    # This runs EVERY time you refresh the page
    df_fresh = load_data()
    
    return html.Div([
        html.H3("MT5 Data Labeler", style={'textAlign': 'center', 'fontFamily': 'Arial'}),
        
        # CONTROL BAR
        html.Div([
            # Navigation
            html.Button('Previous', id='btn-prev', n_clicks=0, style={'padding': '5px 15px'}),
            html.Span(id='page-info', style={'fontWeight': 'bold', 'margin': '0 15px'}),
            html.Button('Next', id='btn-next', n_clicks=0, style={'padding': '5px 15px', 'marginRight': '30px'}),
            
            # Jump to Page
            html.Span("Go to:", style={'marginLeft': '20px'}),
            dcc.Input(id='input-page-jump', type='number', min=1, step=1, style={'width': '50px', 'marginLeft': '5px'}),
            html.Button('Go', id='btn-go', n_clicks=0, style={'marginLeft': '5px', 'marginRight': '40px'}),

            # Save Button
            html.Button('Save Progress', id='btn-save', n_clicks=0, 
                       style={'backgroundColor': 'green', 'color': 'white', 'fontWeight': 'bold', 'padding': '5px 15px'}),
            html.Span(id='save-status', style={'marginLeft': '10px', 'color': 'green', 'fontWeight': 'bold'})
        ], style={'textAlign': 'center', 'marginBottom': '10px', 'backgroundColor': '#f0f0f0', 'padding': '10px'}),

        # CHART
        dcc.Graph(id='candle-chart', style={'height': '80vh'}),
        
        # STORES (Memory)
        dcc.Store(id='store-data', data=df_fresh.to_dict('records')),
        dcc.Store(id='store-page', data=0)
    ])

# Set the layout to the function, not the result
app.layout = serve_layout

# ==========================================
# CALLBACK
# ==========================================
@app.callback(
    [Output('candle-chart', 'figure'),
     Output('store-data', 'data'),
     Output('store-page', 'data'),
     Output('page-info', 'children'),
     Output('save-status', 'children'),
     Output('input-page-jump', 'value')],
    
    [Input('btn-prev', 'n_clicks'),
     Input('btn-next', 'n_clicks'),
     Input('btn-go', 'n_clicks'),
     Input('btn-save', 'n_clicks'),
     Input('candle-chart', 'clickData')],
    
    [State('store-data', 'data'),
     State('store-page', 'data'),
     State('input-page-jump', 'value')]
)
def update_all(btn_prev, btn_next, btn_go, btn_save, clickData, 
               current_data, current_page, jump_value):
    
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else 'No Trigger'

    # Reconstruct DataFrame
    df = pd.DataFrame(current_data)
    # Ensure date format is correct for Plotly
    df['time'] = pd.to_datetime(df['time'])
    
    total_pages = math.ceil(len(df) / PAGE_SIZE) if len(df) > 0 else 1
    msg = ""

    # --- 1. HANDLING NAVIGATION ---
    if trigger_id == 'btn-prev':
        current_page = max(0, current_page - 1)
    elif trigger_id == 'btn-next':
        current_page = min(total_pages - 1, current_page + 1)
    elif trigger_id == 'btn-go' and jump_value is not None:
        target_page = int(jump_value) - 1
        if 0 <= target_page < total_pages:
            current_page = target_page

    # --- 2. HANDLING SAVE ---
    if trigger_id == 'btn-save':
        df.to_csv(OUTPUT_FILE, index=False)
        msg = "Saved!"

    # --- 3. HANDLING TOGGLE (LABEL/UNLABEL) ---
    if trigger_id == 'candle-chart' and clickData:
        clicked_x = clickData['points'][0]['x']
        
        # Find the exact row with this timestamp
        mask = df['time'] == clicked_x
        if mask.any():
            # Get current value (True/False)
            current_val = df.loc[mask, 'label_breakout'].values[0]
            
            # Flip it! (If True -> False. If False -> True)
            df.loc[mask, 'label_breakout'] = not current_val

    # --- 4. SLICING & DRAWING ---
    start_idx = current_page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    df_page = df.iloc[start_idx:end_idx].copy()

    # Base Candle Chart
    fig = go.Figure(data=[go.Candlestick(
        x=df_page['time'],
        open=df_page['open'], high=df_page['high'],
        low=df_page['low'], close=df_page['close'],
        name='OHLC'
    )])

    # Draw Blue Triangles ONLY for rows where label_breakout == True
    labeled_page = df_page[df_page['label_breakout'] == True]
    if not labeled_page.empty:
        fig.add_trace(go.Scatter(
            x=labeled_page['time'], 
            y=labeled_page['high'], 
            mode='markers',
            marker=dict(symbol='triangle-down', size=15, color='blue'),
            name='Breakout'
        ))

    # Layout Updates (Preserve Zoom)
    fig.update_layout(
        uirevision=f'page-{current_page}',  # Resets zoom only when page changes
        title=f'Page {current_page + 1} of {total_pages}',
        xaxis_rangeslider_visible=False,
        dragmode='pan',
        margin=dict(l=40, r=40, t=40, b=40)
    )

    page_info_text = f"Page {current_page + 1} / {total_pages}"

    # Return Data
    return fig, df.to_dict('records'), current_page, page_info_text, msg, (current_page + 1)

if __name__ == '__main__':
    app.run(debug=True)