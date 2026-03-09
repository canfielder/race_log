def get_styles(palette):
    return f"""
    <style>
        .stApp {{ background-color: {palette['vanilla']}10; }} 
        h1, h2, h3 {{ color: {palette['ink_black']}; font-family: 'serif'; }}
        [data-testid="stMetricLabel"] p {{
            font-size: 1.2rem !important;
            color: {palette['dark_teal']} !important;
        }}
    </style>
    """

def get_cluster_css(palette):
        return f"""
        <style>
            /* Small clusters (Pearl Aqua / Dark Cyan) */
            .marker-cluster-small {{
                background-color: {palette['pearl_aqua']}aa !important;
            }}
            .marker-cluster-small div {{
                background-color: {palette['dark_cyan']}aa !important;
                color: {palette['ink_black']} !important;
                /* Standard Sans-Serif Stack */
                font-family: 'Arial', 'Helvetica', sans-serif !important;
                font-size: 13px !important;
                font-weight: 700 !important;
                border: 1px solid {palette['ink_black']}22;
            }}
            
            /* Medium clusters (Vanilla / Orange) */
            .marker-cluster-medium {{
                background-color: {palette['vanilla']}aa !important;
            }}
            .marker-cluster-medium div {{
                background-color: {palette['orange']}aa !important;
                color: {palette['ink_black']} !important;
                font-family: 'Arial', 'Helvetica', sans-serif !important;
                font-size: 13px !important;
                font-weight: 700 !important;
                border: 1px solid {palette['ink_black']}22;
            }}

            /* General Cluster Shape & Alignment */
            .marker-cluster div {{
                width: 28px !important;
                height: 28px !important;
                margin-left: 6px !important;
                margin-top: 6px !important;
                text-align: center !important;
                border-radius: 50% !important;
                line-height: 28px !important;
            }}
        </style>
        """


def get_marker_css(palette):
    return f"""
        <style>
            .heritage-pin {{
                display: flex;
                justify-content: center;
                align-items: center;
                width: 30px;
                height: 30px;
                background-color: {palette['dark_teal']};
                border: 2px solid {palette['ink_black']};
                border-radius: 50% 50% 50% 0;
                transform: rotate(-45deg);
                margin-top: -15px;
                margin-left: -15px;
            }}
            .heritage-pin i {{
                transform: rotate(45deg);
                color: white;
                font-size: 14px;
            }}
        </style>
    """