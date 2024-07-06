import sys
import networkx as nx
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QTextEdit, QPushButton, QComboBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.collections import PathCollection
import colorsys

def generate_colors(n):
    HSV_tuples = [(x * 1.0 / n, 0.5, 0.5) for x in range(n)]
    RGB_tuples = list(map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples))
    return ['#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255)) for r, g, b in RGB_tuples]

class CBAVisualization(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CBA System Visualization")
        self.setGeometry(100, 100, 1800, 1000)

        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # Left panel for graph
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        main_layout.addWidget(left_panel, 2)

        # Navigation controls
        nav_layout = QHBoxLayout()
        self.area_selector = QComboBox()
        self.area_selector.currentTextChanged.connect(self.change_area)
        nav_layout.addWidget(QLabel("Select Functional Area:"))
        nav_layout.addWidget(self.area_selector)
        left_layout.addLayout(nav_layout)

        # Graph visualization
        self.figure, self.ax = plt.subplots(figsize=(12, 10))
        self.canvas = FigureCanvas(self.figure)
        left_layout.addWidget(self.canvas)

        self.toolbar = NavigationToolbar(self.canvas, self)
        left_layout.addWidget(self.toolbar)

        # Right panel for asset details
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        main_layout.addWidget(right_panel, 1)

        right_layout.addWidget(QLabel("Area/Asset Details:"))
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        right_layout.addWidget(self.details_text)

        self.create_graph()
        self.populate_area_selector()
        self.current_area = "Overview"
        self.draw_graph()

        self.canvas.mpl_connect('pick_event', self.on_pick)

    def create_graph(self):
        print("Creating graph")
        self.G = nx.DiGraph()
        self.overview_G = nx.DiGraph()

        # Define all assets with expanded details (as before)
        self.assets = {
            "Portico": {
                "area": "Pre-Sales",
                "description": "Cloud-based fleet design and asset utilization tool for Managed Print Services.",
                "key_features": [
                    "Fleet design optimization",
                    "Asset utilization analysis",
                    "TCO calculation",
                    "Proposal generation"
                ],
                "related_systems": ["DART", "HP Dynamics"],
                "data_flow": "Sends optimized fleet designs to DART for pricing",
                "business_impact": "Improves win rates by providing optimized fleet designs and accurate TCO projections"
            },
            "HP Dynamics": {
                "area": "Sales",
                "description": "Sales platform for relationship management and opportunity creation.",
                "key_features": [
                    "Customer relationship management",
                    "Opportunity tracking",
                    "Sales pipeline management",
                    "Integration with other CBA tools"
                ],
                "related_systems": ["DART", "Portico"],
                "data_flow": "Receives customer data from Portico, sends opportunity data to DART",
                "business_impact": "Centralizes customer information and streamlines the sales process"
            },
            "DART": {
                "area": "Sales",
                "description": "Deal Analysis Response Tool for creating CBA-compliant deals and pricing.",
                "key_features": [
                    "Pricing engine",
                    "Deal structuring",
                    "Compliance checking",
                    "Approval workflow"
                ],
                "related_systems": ["Portico", "HP Dynamics", "MPC"],
                "data_flow": "Receives fleet designs from Portico, pricing requests from HP Dynamics, sends structured deals to MPC",
                "business_impact": "Ensures consistent and compliant pricing across all deals"
            },
            "MPC": {
                "area": "Sales",
                "description": "Managed Print Central, a web-based application for partners to create and manage CBA contracts.",
                "key_features": [
                    "Contract creation and management",
                    "Partner portal",
                    "Integration with billing systems"
                ],
                "related_systems": ["DART", "TMC"],
                "data_flow": "Receives structured deals from DART, sends contract information to TMC",
                "business_impact": "Streamlines contract management and improves partner experience"
            },
            "TMC": {
                "area": "Transition Management",
                "description": "Transition Management Central, manages transition to account/contract management through service delivery.",
                "key_features": [
                    "Project management",
                    "Service delivery coordination",
                    "Status tracking and reporting"
                ],
                "related_systems": ["MPC", "Broker"],
                "data_flow": "Receives contract information from MPC, sends transition plans to Broker",
                "business_impact": "Ensures smooth transition from sales to service delivery, improving customer satisfaction"
            },
            "Broker": {
                "area": "Transition Management",
                "description": "Workflow engine for onboarding data, bridging TMC, SAP, and ITSM.",
                "key_features": [
                    "Data transformation",
                    "System integration",
                    "Workflow automation"
                ],
                "related_systems": ["TMC", "ITSM ServiceNow"],
                "data_flow": "Receives transition plans from TMC, sends onboarding data to ITSM ServiceNow",
                "business_impact": "Automates and streamlines the onboarding process, reducing errors and improving efficiency"
            },
            "ITSM ServiceNow": {
                "area": "Asset Management",
                "description": "IT Service Management platform for managing assets and services.",
                "key_features": [
                    "Asset tracking",
                    "Service catalog",
                    "Incident management",
                    "Change management"
                ],
                "related_systems": ["Broker", "MS4"],
                "data_flow": "Receives onboarding data from Broker, sends asset information to MS4",
                "business_impact": "Centralizes asset management and improves service delivery efficiency"
            },
            "MS4": {
                "area": "Entitlement, Billing & Invoicing",
                "description": "Master data replication system.",
                "key_features": [
                    "Data synchronization",
                    "Master data management",
                    "Data quality assurance"
                ],
                "related_systems": ["ITSM ServiceNow", "S4"],
                "data_flow": "Receives asset information from ITSM ServiceNow, replicates master data to S4",
                "business_impact": "Ensures data consistency across systems, improving reporting accuracy"
            },
            "S4": {
                "area": "Entitlement, Billing & Invoicing",
                "description": "SAP S/4HANA system for financial processes.",
                "key_features": [
                    "Financial accounting",
                    "Contract management",
                    "Billing and invoicing"
                ],
                "related_systems": ["MS4", "BRIM"],
                "data_flow": "Receives master data from MS4, sends billing information to BRIM",
                "business_impact": "Centralizes financial processes and improves financial reporting"
            },
            "BRIM": {
                "area": "Entitlement, Billing & Invoicing",
                "description": "Billing and Revenue Innovation Management system.",
                "key_features": [
                    "Complex billing scenarios",
                    "Revenue recognition",
                    "Subscription management"
                ],
                "related_systems": ["S4", "CC/CM"],
                "data_flow": "Receives billing information from S4, sends charging data to CC/CM",
                "business_impact": "Enables flexible billing models and improves revenue management"
            },
            "CC/CM": {
                "area": "Entitlement, Billing & Invoicing",
                "description": "Convergent Charging and Mediation system.",
                "key_features": [
                    "Usage-based charging",
                    "Real-time rating",
                    "Mediation of usage data"
                ],
                "related_systems": ["BRIM", "Usage Service"],
                "data_flow": "Receives charging data from BRIM, processes usage data from Usage Service",
                "business_impact": "Enables accurate usage-based billing and improves billing flexibility"
            },
            "CDAX": {
                "area": "Case Management",
                "description": "Custom version of Microsoft Dynamics CRM for HP Customer Support.",
                "key_features": [
                    "Case tracking",
                    "Customer interaction history",
                    "Knowledge base integration",
                    "Service level agreement (SLA) tracking"
                ],
                "related_systems": ["DCC", "ITSM ServiceNow"],
                "data_flow": "Receives customer support requests from DCC, sends case information to ITSM ServiceNow",
                "business_impact": "Improves customer support efficiency and enhances customer satisfaction"
            },
            "DCC": {
                "area": "Customer Portal",
                "description": "Device Control Center, interface for customers to view and manage their fleet.",
                "key_features": [
                    "Fleet overview",
                    "Device status monitoring",
                    "Supply ordering",
                    "Service request initiation"
                ],
                "related_systems": ["CDAX", "ARC"],
                "data_flow": "Sends customer requests to CDAX, receives supply status from ARC",
                "business_impact": "Enhances customer experience and reduces support calls through self-service capabilities"
            },
            "ARC": {
                "area": "Replenishment",
                "description": "Automated Reordering of Consumables, manages supplies orders and distribution.",
                "key_features": [
                    "Automated supply ordering",
                    "Inventory management",
                    "Order tracking",
                    "Predictive analytics for supply needs"
                ],
                "related_systems": ["DCC", "HP Direct"],
                "data_flow": "Receives supply status from DCC, sends orders to HP Direct",
                "business_impact": "Reduces supply outages and optimizes inventory levels, improving customer satisfaction"
            },
            "HP Direct": {
                "area": "Replenishment",
                "description": "Direct fulfillment service for supplies orders.",
                "key_features": [
                    "Order processing",
                    "Warehouse management",
                    "Shipping and logistics",
                    "Return handling"
                ],
                "related_systems": ["ARC", "Usage Service"],
                "data_flow": "Receives orders from ARC, sends fulfillment data to Usage Service",
                "business_impact": "Ensures timely delivery of supplies, reducing customer downtime"
            },
            "Usage Service": {
                "area": "Telemetry Processor",
                "description": "Processes telemetry data, analyzes supplies levels, and determines fulfillment needs.",
                "key_features": [
                    "Real-time data processing",
                    "Supplies level monitoring",
                    "Usage pattern analysis",
                    "Predictive maintenance"
                ],
                "related_systems": ["HP Direct", "Fulfillment Service"],
                "data_flow": "Receives telemetry data from devices, sends usage data to Fulfillment Service",
                "business_impact": "Enables proactive supply replenishment and reduces device downtime"
            },
            "Fulfillment Service": {
                "area": "Telemetry Processor",
                "description": "Determines auto-replenishment needs based on usage data.",
                "key_features": [
                    "Auto-replenishment algorithms",
                    "Supply chain optimization",
                    "Demand forecasting",
                    "Integration with ARC"
                ],
                "related_systems": ["Usage Service", "ARC"],
                "data_flow": "Receives usage data from Usage Service, sends replenishment requests to ARC",
                "business_impact": "Optimizes supply chain efficiency and reduces costs associated with overstocking or stockouts"
            },
            "HP SDS": {
                "area": "Device Connectivity",
                "description": "Smart Device Services, provides advanced monitoring and management capabilities.",
                "key_features": [
                    "Remote device monitoring",
                    "Predictive maintenance",
                    "Firmware updates",
                    "Security management"
                ],
                "related_systems": ["JAM", "Usage Service"],
                "data_flow": "Collects device data, sends to JAM and Usage Service",
                "business_impact": "Improves device uptime and reduces service costs through predictive maintenance"
            },
            "JAM": {
                "area": "Device Connectivity",
                "description": "JetAdvantage Management, part of the device connectivity and management ecosystem.",
                "key_features": [
                    "Device fleet management",
                    "Security policy enforcement",
                    "Remote configuration",
                    "Reporting and analytics"
                ],
                "related_systems": ["HP SDS", "Stratus"],
                "data_flow": "Receives device data from HP SDS, sends management commands to Stratus",
                "business_impact": "Centralizes device management, improving operational efficiency and security"
            },
            "Stratus": {
                "area": "Device Connectivity",
                "description": "Handles IoT connectivity and device management in the cloud.",
                "key_features": [
                    "Cloud-based device connectivity",
                    "Data aggregation",
                    "Device provisioning",
                    "Scalable IoT infrastructure"
                ],
                "related_systems": ["JAM", "JAMc"],
                "data_flow": "Receives management commands from JAM, sends device data to JAMc",
                "business_impact": "Provides scalable and reliable infrastructure for device connectivity and management"
            },
            "JAMc": {
                "area": "Device Connectivity",
                "description": "JAM Connector, facilitates connection and management of devices.",
                "key_features": [
                    "Device discovery",
                    "Connection brokering",
                    "Protocol translation",
                    "Data normalization"
                ],
                "related_systems": ["Stratus", "FM Audit Server"],
                "data_flow": "Receives device data from Stratus, sends normalized data to FM Audit Server",
                "business_impact": "Enables seamless integration of diverse device types into the management ecosystem"
            },
            "FM Audit Server": {
                "area": "Device Connectivity",
                "description": "Fleet Management Auditing server for comprehensive data collection.",
                "key_features": [
                    "Device data collection",
                    "Usage auditing",
                    "Compliance checking",
                    "Historical data storage"
                ],
                "related_systems": ["JAMc", "FM Audit Agent"],
                "data_flow": "Receives normalized data from JAMc, sends audit instructions to FM Audit Agent",
                "business_impact": "Provides accurate and comprehensive fleet data for billing and management purposes"
            },
            "FM Audit Agent": {
                "area": "Device Connectivity",
                "description": "Local data collection agent for FM Audit.",
                "key_features": [
                    "Local device discovery",
                    "Secure data collection",
                    "Offline data caching",
                    "Bandwidth optimization"
                ],
                "related_systems": ["FM Audit Server", "BIRD"],
                "data_flow": "Receives audit instructions from FM Audit Server, sends collected data to BIRD",
                "business_impact": "Ensures accurate data collection even in challenging network environments"
            },
            "BIRD": {
                "area": "Business Intelligence",
                "description": "Business Intelligence Reporting Dashboard, used for various reporting and data management tasks.",
                "key_features": [
                    "Data visualization",
                    "Custom report generation",
                    "KPI tracking",
                    "Predictive analytics"
                ],
                "related_systems": ["FM Audit Agent", "Fleet Ops"],
                "data_flow": "Receives collected data from FM Audit Agent, sends analytics to Fleet Ops",
                "business_impact": "Provides actionable insights for decision-making and business optimization"
            },
            "Fleet Ops": {
                "area": "Fleet Operations",
                "description": "Manages device operations, including remote diagnostics and remediation.",
                "key_features": [
                    "Remote diagnostics",
                    "Proactive maintenance",
                    "Fleet optimization",
                    "Service dispatch management"
                ],
                "related_systems": ["BIRD", "HP SDS"],
                "data_flow": "Receives analytics from BIRD, sends operational commands to HP SDS",
                "business_impact": "Maximizes fleet uptime and efficiency through proactive management and optimization"
            }
        }

        # Group assets by functional area
        self.functional_areas = {}
        for asset, data in self.assets.items():
            area = data['area']
            if area not in self.functional_areas:
                self.functional_areas[area] = []
            self.functional_areas[area].append(asset)

        # Add nodes to the graph
        for asset, data in self.assets.items():
            self.G.add_node(asset, **data)
            print(f"Added node: {asset}")

        # Add nodes to the overview graph
        for area in self.functional_areas:
            self.overview_G.add_node(area)

        # Define and add edges
        edges = [
            ("Portico", "DART"),
            ("Portico", "HP Dynamics"),
            ("HP Dynamics", "DART"),
            ("DART", "MPC"),
            ("MPC", "TMC"),
            ("TMC", "Broker"),
            ("Broker", "ITSM ServiceNow"),
            ("ITSM ServiceNow", "MS4"),
            ("MS4", "S4"),
            ("S4", "BRIM"),
            ("BRIM", "CC/CM"),
            ("CC/CM", "Usage Service"),
            ("CDAX", "DCC"),
            ("DCC", "ARC"),
            ("ARC", "HP Direct"),
            ("HP Direct", "Usage Service"),
            ("Usage Service", "Fulfillment Service"),
            ("Fulfillment Service", "ARC"),
            ("HP SDS", "JAM"),
            ("JAM", "Stratus"),
            ("Stratus", "JAMc"),
            ("JAMc", "FM Audit Server"),
            ("FM Audit Server", "FM Audit Agent"),
            ("FM Audit Agent", "BIRD"),
            ("BIRD", "Fleet Ops"),
            ("Fleet Ops", "HP SDS"),
            ("ITSM ServiceNow", "CDAX"),
            ("DCC", "CDAX"),
            ("Usage Service", "HP SDS"),
            ("JAM", "HP SDS"),
            ("BRIM", "S4"),
            ("CC/CM", "BRIM"),
            ("Fulfillment Service", "HP Direct"),
            ("ARC", "Fulfillment Service"),
            ("JAMc", "Stratus"),
            ("FM Audit Server", "JAMc"),
            ("BIRD", "FM Audit Server"),
            ("Fleet Ops", "BIRD"),
            ("HP SDS", "Fleet Ops"),
            ("CDAX", "ITSM ServiceNow"),
            ("S4", "MS4"),
            ("Usage Service", "CC/CM"),
            ("HP Dynamics", "Portico"),
            ("MPC", "DART"),
            ("TMC", "MPC"),
            ("Broker", "TMC"),
            ("ITSM ServiceNow", "Broker"),
            ("MS4", "ITSM ServiceNow"),
            ("S4", "BRIM"),
            ("CC/CM", "BRIM"),
            ("DCC", "CDAX"),
            ("ARC", "DCC"),
            ("HP Direct", "ARC"),
            ("Usage Service", "HP Direct"),
            ("Fulfillment Service", "Usage Service"),
            ("JAM", "HP SDS"),
            ("Stratus", "JAM"),
            ("JAMc", "Stratus"),
            ("FM Audit Server", "JAMc"),
            ("FM Audit Agent", "FM Audit Server"),
            ("BIRD", "FM Audit Agent"),
            ("Fleet Ops", "BIRD")
        ]

        self.G.add_edges_from(edges)
        print(f"Added {len(edges)} edges")

        # Add edges to the overview graph
        for source, target in edges:
            source_area = self.assets[source]['area']
            target_area = self.assets[target]['area']
            if source_area != target_area:
                self.overview_G.add_edge(source_area, target_area)

        print(f"Graph created with {self.G.number_of_nodes()} nodes and {self.G.number_of_edges()} edges")
        print(f"Overview graph created with {self.overview_G.number_of_nodes()} nodes and {self.overview_G.number_of_edges()} edges")

    def populate_area_selector(self):
        self.area_selector.addItem("Overview")
        self.area_selector.addItems(sorted(self.functional_areas.keys()))

    def change_area(self, area):
        self.current_area = area
        self.draw_graph()

    def draw_graph(self):
        print(f"Drawing graph for {self.current_area}")
        self.ax.clear()

        if self.current_area == "Overview":
            self.draw_overview()
        else:
            self.draw_specific_area()

        self.ax.set_title(f"CBA System Visualization - {self.current_area}")
        self.ax.axis('off')
        self.canvas.draw()

    def draw_overview(self):
        pos = nx.spring_layout(self.overview_G, k=0.5, iterations=50)
        
        colors = generate_colors(len(self.overview_G))
        color_map = dict(zip(self.overview_G.nodes(), colors))
        
        nx.draw_networkx_nodes(self.overview_G, pos, node_size=3000, node_color=list(color_map.values()), alpha=0.8, ax=self.ax)
        nx.draw_networkx_labels(self.overview_G, pos, font_size=10, ax=self.ax)
        nx.draw_networkx_edges(self.overview_G, pos, edge_color='gray', arrows=True, ax=self.ax, arrowsize=20, width=1.5)

        self.node_positions = pos

    def draw_specific_area(self):
        nodes = self.functional_areas[self.current_area]
        self.subgraph = self.G.subgraph(nodes)

        pos = nx.spring_layout(self.subgraph, k=0.5, iterations=50)
        
        color = generate_colors(1)[0]
        node_colors = [color] * len(self.subgraph)
        
        self.node_collection = nx.draw_networkx_nodes(self.subgraph, pos, node_size=3000, node_color=node_colors, ax=self.ax, alpha=0.8)
        self.node_collection.set_picker(5)
        nx.draw_networkx_labels(self.subgraph, pos, font_size=10, ax=self.ax)
        nx.draw_networkx_edges(self.subgraph, pos, edge_color='gray', arrows=True, ax=self.ax, arrowsize=20, width=1.5)

        self.node_positions = pos

    def on_pick(self, event):
        if self.current_area == "Overview":
            if isinstance(event.artist, PathCollection):
                ind = event.ind[0]
                area = list(self.overview_G.nodes())[ind]
                self.show_area_details(area)
        else:
            if isinstance(event.artist, PathCollection):
                ind = event.ind[0]
                node = list(self.subgraph.nodes())[ind]
                self.show_asset_details(node)

    def show_area_details(self, area):
        details = f"Functional Area: {area}\n\n"
        details += f"Assets in this area:\n"
        for asset in self.functional_areas[area]:
            details += f"- {asset}\n"
        details += f"\nConnected Areas:\n"
        for neighbor in self.overview_G.neighbors(area):
            details += f"- {neighbor}\n"

        self.details_text.setText(details)

    def show_asset_details(self, node):
        asset_data = self.assets[node]
        details = f"Asset: {node}\n\n"
        details += f"Functional Area: {asset_data['area']}\n\n"
        details += f"Description: {asset_data['description']}\n\n"
        details += "Key Features:\n"
        for feature in asset_data['key_features']:
            details += f"- {feature}\n"
        details += f"\nRelated Systems: {', '.join(asset_data['related_systems'])}\n\n"
        details += f"Data Flow: {asset_data['data_flow']}\n\n"
        details += f"Business Impact: {asset_data['business_impact']}"

        self.details_text.setText(details)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = CBAVisualization()
    main_window.show()
    sys.exit(app.exec_())