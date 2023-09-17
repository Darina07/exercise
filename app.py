import dash
from dash import dcc, html
from dash import dash_table
from dash_table import DataTable, FormatTemplate
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff  # Import for creating the heatmap
from sklearn.preprocessing import LabelEncoder
from database import MySQLConnection  # Assuming you have your MySQL connection class in 'database.py'

app = dash.Dash(__name__)


def load_data():
    db = MySQLConnection.get_instance()

    # Example SQL query to fetch data from the 'candidates' table
    query = """
        SELECT c.id, c.title, c.first_name, c.last_name, c.location, c.level_of_seniority,
               c.created_at, c.rate, c.rate_onsite, p.position AS position, 
               c.nationality, c.send_rate, c.send_rate_onsite, c.cv_link, c.email, c.linkedin, c.description
        FROM candidates AS c
        LEFT JOIN positions AS p ON c.position = p.id
    """

    result = db.execute_query(query)

    # Convert the result to a pandas DataFrame
    df = pd.DataFrame(result, columns=["id", "title", "first_name", "last_name", "location", "level_of_seniority",
                                       "created_at", "rate", "rate_onsite", "position", "nationality", "send_rate",
                                       "send_rate_onsite", "cv_link", "email", "linkedin", "description"])

    return df


# Calculate the candidate count by location
df = load_data()
location_counts = df['location'].value_counts().reset_index()
location_counts.columns = ['location', 'count']

# Create a label encoder for 'position' and 'location'
label_encoder = LabelEncoder()

# Apply label encoding to the 'position' and 'location' columns
df['position_encoded'] = label_encoder.fit_transform(df['position'])
df['location_encoded'] = label_encoder.fit_transform(df['location'])

# Calculate the correlation matrix, including the encoded columns
correlation_matrix = df[['rate', 'position_encoded', 'location_encoded']].corr()

# Create the bar chart using Plotly Express
fig = px.bar(location_counts, x='location', y='count', title='Consultants by Location')


# Create a function to calculate statistics
def calculate_statistics(data):
    # Calculate the total number of candidates and mean and mode rate by title
    statistics_by_title = data.groupby('title').agg(
        total_number_candidates=('title', 'count'),
        mean_rate=('rate', 'mean'),
        mode_rate=('rate', lambda x: x.mode().iloc[0] if not x.mode().empty else None)
    ).reset_index()

    return statistics_by_title


# Get the statistics
statistics_by_title = calculate_statistics(df)


def create_correlation_heatmap(data):
    # Get the column names as a list of strings
    column_names = data.columns.tolist()

    # Create a heatmap of the correlation matrix with a valid colorscale
    fig5 = ff.create_annotated_heatmap(
        z=data.values,
        x=column_names,
        y=column_names,
        colorscale='Viridis',  # Use a valid colorscale here
        showscale=True,
        colorbar=dict(title='Correlation'),
    )
    fig5.update_layout(title='Pearson Correlation Heatmap', xaxis_title='Variables', yaxis_title='Variables')
    return fig5


def create_scatter_plot(data):
    fig = px.scatter(data, x='rate', y='location', color='position', hover_name="nationality", title='Consultants by Location and Rate',  size_max=60)
    return fig

def create_pie_chart(data):
    nationality_counts = data['nationality'].value_counts().reset_index()
    nationality_counts.columns = ['nationality', 'count']
    fig1 = px.pie(nationality_counts, names='nationality', values='count', title='Consultants by Nationality')
    return fig1


def candidates_added_per_week(data):
    # Convert the 'created_at' column to a datetime format
    data['created_at'] = pd.to_datetime(data['created_at'])

    # Calculate the number of candidates added each week
    weekly_counts = data.resample('W-Mon', on='created_at').size().reset_index()
    weekly_counts.columns = ['Week', 'Candidates Added']

    return weekly_counts


def create_line_plot(data):
    fig2 = px.line(data, x='Week', y='Candidates Added', title='Candidates Added Per Week')
    return fig2


app.layout = html.Div([
    html.H1("Available Consultants"),
    DataTable(
        id='table',
        columns=[
            {"name": col, "id": col, "type": "text", "presentation": "input"} if col not in ["rate", "rate_onsite",
                                                                                             "send_rate",
                                                                                             "send_rate_onsite"] else
            {"name": col, "id": col, "type": "numeric", "format": FormatTemplate.money(2)}
            # Format selected columns as currency
            for col in df.columns
        ],
        data=df.to_dict('records'),
        sort_action="native",
        filter_action="native",
        page_size=10  # Number of rows per page
    ),
    html.Div([
        dcc.Markdown("### Statistics"),

        # Display total number of candidates and mean and mode rate by title
        html.P("Total Number of Candidates, Mean Rate, and Mode Rate by Title:"),
        DataTable(
            id='statistics-by-title',
            columns=[
                {"name": "Title", "id": "title"},
                {"name": "Total Number of Candidates", "id": "total_number_candidates"},
                {"name": "Mean Rate", "id": "mean_rate", "type": "numeric", "format": FormatTemplate.money(2)},
                {"name": "Mode Rate", "id": "mode_rate", "type": "numeric", "format": FormatTemplate.money(2)},
            ],
            data=statistics_by_title.to_dict('records'),
            sort_action="native",
        ),
    ]),
    dcc.Graph(id='scatter-plot', figure=create_scatter_plot(load_data())),
    dcc.Graph(figure=fig),
    dcc.Graph(id='pie-chart', figure=create_pie_chart(load_data())),
    dcc.Graph(id='line-plot', figure=create_line_plot(candidates_added_per_week(load_data()))),
    dcc.Graph(id='correlation-heatmap', figure=create_correlation_heatmap(correlation_matrix))
])

if __name__ == '__main__':
    app.run_server(debug=True)
