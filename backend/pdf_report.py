import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_pdf_report(summary_data: dict, output_filepath: str = "dam_break_report.pdf") -> str:
    """
    Generates a professional executive PDF report for Dam Break Inundation Analysis.
    """
    doc = SimpleDocTemplate(
        output_filepath,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Palette Definition
    PRIMARY_COLOR = colors.HexColor("#1e293b")  # Dark Slate
    ACCENT_COLOR = colors.HexColor("#0284c7")   # Deep Sky Blue
    TEXT_COLOR = colors.HexColor("#334155")     # Neutral Muted Text
    
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=20, leading=24,
        textColor=PRIMARY_COLOR, spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10, leading=13,
        textColor=ACCENT_COLOR, spaceAfter=15
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading', parent=styles['Heading2'],
        fontName='Helvetica-Bold', fontSize=13, leading=16,
        textColor=PRIMARY_COLOR, spaceBefore=12, spaceAfter=8
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9.5, leading=14,
        textColor=TEXT_COLOR
    )

    story = []

    # Title & Subtitle Header
    story.append(Paragraph("HYDRODYNAMIC DAM BREAK INUNDATION REPORT", title_style))
    story.append(Paragraph("Automated Early Warning & Spatial Emergency Response Assessment | SIH-161", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT_COLOR, spaceAfter=15))

    # General Information Overview
    story.append(Paragraph("1. System & Scenario Specifications", section_heading))
    spec_data = [
        [Paragraph("<b>Target Dam / Structure:</b>", body_style), Paragraph(str(summary_data.get("dam_name", "Tehri Dam")), body_style),
         Paragraph("<b>Location / River:</b>", body_style), Paragraph(f"{summary_data.get('state', 'Uttarakhand')} ({summary_data.get('river', 'Bhagirathi')})", body_style)],
        [Paragraph("<b>Simulation Horizon:</b>", body_style), Paragraph(f"{summary_data.get('simulation_hours', 3.0)} Hours", body_style),
         Paragraph("<b>Spatial Grid Size:</b>", body_style), Paragraph(str(summary_data.get("grid_resolution", "50 x 50 (2D Grid)")), body_style)],
    ]
    spec_table = Table(spec_data, colWidths=[1.5*inch, 2.0*inch, 1.5*inch, 2.2*inch])
    spec_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(spec_table)
    story.append(Spacer(1, 10))

    # Breach & Peak Discharge Hydraulics
    story.append(Paragraph("2. Breach Mechanics & Hydrodynamic Metrics", section_heading))
    metrics_data = [
        [Paragraph("<b>Metric Parameter</b>", body_style), Paragraph("<b>Simulated Value</b>", body_style), Paragraph("<b>Engineering Impact / Assessment</b>", body_style)],
        [Paragraph("Average Breach Width (b_avg)", body_style), Paragraph(f"<b>{summary_data.get('breach_width_m', 0):.2f} m</b>", body_style), Paragraph("Calculated using Froehlich empirical breach formulations.", body_style)],
        [Paragraph("Breach Formation Time (t_f)", body_style), Paragraph(f"<b>{summary_data.get('formation_time_min', 0):.2f} mins</b>", body_style), Paragraph("Time required for structural failure geometry to stabilize.", body_style)],
        [Paragraph("Peak Breach Discharge (Q_peak)", body_style), Paragraph(f"<b>{summary_data.get('peak_discharge_m3s', 0):,.2f} m³/s</b>", body_style), Paragraph("Maximum instantaneous outflow wave energy.", body_style)],
        [Paragraph("Total Inundated Coverage Area", body_style), Paragraph(f"<b>{summary_data.get('total_flooded_area_km2', 0):.2f} km²</b>", body_style), Paragraph("Downstream land surface submerged (>0.1m depth).", body_style)],
    ]
    metrics_table = Table(metrics_data, colWidths=[2.2*inch, 1.8*inch, 3.2*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f1f5f9")]),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 10))

    # Downstream Settlement Impact Summary
    story.append(Paragraph("3. Downstream Settlement Hazard Assessment", section_heading))
    settlements = summary_data.get("risk_summary", [
        {"name": "Rampur Village", "population": 1250, "water_depth_m": 0.85, "risk_level": "WARNING"},
        {"name": "Govindpur", "population": 3400, "water_depth_m": 2.10, "risk_level": "EVACUATE"}
    ])
    
    risk_table_data = [
        [Paragraph("<b>Settlement Name</b>", body_style), Paragraph("<b>Population at Risk</b>", body_style), Paragraph("<b>Peak Depth (m)</b>", body_style), Paragraph("<b>Action / Status Badge</b>", body_style)]
    ]
    
    for s in settlements:
        status_color = colors.HexColor("#10b981") # SAFE (Green)
        if s["risk_level"] == "WARNING":
            status_color = colors.HexColor("#f59e0b") # WARNING (Orange)
        elif s["risk_level"] == "EVACUATE":
            status_color = colors.HexColor("#ef4444") # EVACUATE (Red)
            
        status_p = Paragraph(f"<font color='{status_color.hexval()}'><b>{s['risk_level']}</b></font>", body_style)
        risk_table_data.append([
            Paragraph(s["name"], body_style),
            Paragraph(f"{s['population']:,}", body_style),
            Paragraph(f"{s['water_depth_m']:.2f} m", body_style),
            status_p
        ])
        
    risk_table = Table(risk_table_data, colWidths=[2.2*inch, 1.6*inch, 1.6*inch, 1.8*inch])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#334155")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 15))

    # Disclaimer / Footer Notice
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
    story.append(Paragraph("<i>Notice: This automated report is produced by the SIH-161 2D Shallow Water Hydrodynamic Simulation System for emergency response planning and evacuation warning purposes.</i>", ParagraphStyle('Footnote', parent=styles['Normal'], fontSize=7.5, leading=10, textColor=colors.HexColor("#64748b"))))

    doc.build(story)
    return output_filepath