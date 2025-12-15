import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import io
import base64
import textwrap

# Set backend to avoid GUI issues in Docker
plt.switch_backend('Agg')

class ChartFactory:
    @staticmethod
    def _to_base64(fig):
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return f"data:image/png;base64,{img_str}"

    @staticmethod
    def generate_bar_chart(labels, scores, color="#4a90e2"):
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(labels, scores, color=color, width=0.6)
        
        plt.xticks(rotation=45, ha='right')

        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{int(height)}%', ha='center', va='bottom', fontsize=9)
        
        ax.set_ylim(0, 110)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        return ChartFactory._to_base64(fig)

    @staticmethod
    def generate_radar_chart(categories, values):
        N = len(categories)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]
        values_aug = values + values[:1]
        
        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_subplot(111, polar=True)
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        
        plt.xticks(angles[:-1], categories, size=9)
        ax.tick_params(axis='x', pad=20)
        
        ax.set_rlabel_position(0)
        plt.yticks([25, 50, 75, 100], ["25", "50", "75", ""], color="grey", size=7)
        plt.ylim(0, 100)
        
        ax.plot(angles, values_aug, linewidth=2, linestyle='solid', color='#4a90e2')
        ax.fill(angles, values_aug, color='#4a90e2', alpha=0.1)
        return ChartFactory._to_base64(fig)

    @staticmethod
    def generate_radial_bar_chart(labels, scores):
        base_colors = ['#8ED1E6', '#8D8FB9', '#C586B5', '#E78FA2', '#F5E556', '#7FB97A', "#28D4A9"]
        colors_to_use = (base_colors * 2)[:len(labels)]
        
        data = list(zip(scores, labels, colors_to_use))
        data.sort(key=lambda x: x[0])
        
        sorted_scores, sorted_labels, sorted_colors = zip(*data)
        N = len(sorted_scores)
        theta = [(x / 100.0) * 2 * np.pi for x in sorted_scores]
        
        bar_width = 1.0
        gap = 0.1
        inner_radius = 2.0
        radii = [inner_radius + i * (bar_width + gap) for i in range(N)]
        
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})
        
        ax.set_theta_zero_location("S") 
        ax.set_theta_direction(-1)      
        
        bars = ax.bar(
            x=np.zeros(N), 
            height=bar_width, 
            width=theta, 
            bottom=radii, 
            color=sorted_colors, 
            alpha=0.9
        )
        
        ax.axis('off')
        
        for r, v in zip(radii, sorted_scores):
            ax.text(0, r + (bar_width / 2), f"{int(v)}%", 
                    ha='center', va='center', 
                    color='white', fontweight='bold', fontsize=9)
            
        ax.legend(
            bars[::-1], sorted_labels[::-1], 
            loc="center left", 
            bbox_to_anchor=(1.1, 0.5), 
            frameon=False,
            fontsize=9
        )
        
        return ChartFactory._to_base64(fig)

    @staticmethod
    def generate_seven_segment_chart(labels, scores):
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.set_aspect('equal')
        ax.axis('off')

        data_points = [{'label': l, 'value': s} for l, s in zip(labels, scores)]
        num_segments = len(data_points)
        
        base_colors = [
            '#FF5252', '#FFD600', '#00E676', '#00B0FF',
            '#AA00FF', '#FF6D00', '#F50057'
        ]
        colors = (base_colors * 2)[:num_segments]

        max_radius = 1.0
        start_angle = 90

        for i in range(num_segments):
            angle_deg = start_angle - (i * (360 / num_segments))
            angle_rad = np.deg2rad(angle_deg)
            x_end = max_radius * np.cos(angle_rad)
            y_end = max_radius * np.sin(angle_rad)
            ax.plot([0, x_end], [0, y_end], color='black', linewidth=1.5, zorder=10)

        for i, item in enumerate(data_points):
            angle_step = 360 / num_segments
            theta1 = start_angle - ((i + 1) * angle_step)
            theta2 = start_angle - (i * angle_step)
            
            current_radius = (item['value'] / 100.0) * max_radius
            if current_radius < 0.05: current_radius = 0.05

            wedge = patches.Wedge(
                center=(0, 0),
                r=current_radius,
                theta1=theta1,
                theta2=theta2,
                facecolor=colors[i],
                edgecolor=None,
                linewidth=0
            )
            ax.add_patch(wedge)

            mid_angle_deg = (theta1 + theta2) / 2
            mid_angle_rad = np.deg2rad(mid_angle_deg)

            text_r = current_radius * 0.6
            if text_r < 0.2: text_r = 0.25
            
            x_text = text_r * np.cos(mid_angle_rad)
            y_text = text_r * np.sin(mid_angle_rad)
            
            ax.text(x_text, y_text, f"{int(item['value'])}%",
                    ha='center', va='center',
                    fontsize=10, fontweight='bold', color='black')

            label_r = max_radius * 1.15
            label_x = label_r * np.cos(mid_angle_rad)
            label_y = label_r * np.sin(mid_angle_rad)
            
            ax.text(label_x, label_y, item['label'],
                    ha='center', va='center',
                    fontsize=11, fontweight='bold')

        outer_circle = plt.Circle((0, 0), max_radius, color='black', fill=False, linewidth=2, zorder=10)
        ax.add_patch(outer_circle)

        ax.set_xlim(-1.3, 1.3)
        ax.set_ylim(-1.3, 1.3)
        
        return ChartFactory._to_base64(fig)

    @staticmethod
    def generate_variable_radius_chart(labels, scores):
        """
        Generates the Variable Radius Infographic based on provided Logic.
        """
        # 1. Setup Figure
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Set limits
        ax.set_xlim(-1.4, 1.4)
        ax.set_ylim(-1.4, 1.4)

        # 2. Configuration
        num_segments = len(scores)
        start_angle = 90
        gap_size = 2
        
        # Radii Control
        inner_void_r = 0.20
        max_rim_r = 1.05
        
        # Color Palette (Provided Green Teens)
        base_colors = ['#4DB6AC', '#26A69A', '#009688', '#00897B', '#00796B', '#00695C']
        
        # Avoid division by zero if max is 0
        max_value = max(scores) if scores and max(scores) > 0 else 100

        for i, (label, value) in enumerate(zip(labels, scores)):
            # --- A. Angle Calculation ---
            angle_step = 360 / num_segments
            theta_start = start_angle - (i * angle_step) - (gap_size / 2)
            theta_end = start_angle - ((i + 1) * angle_step) + (gap_size / 2)
            
            t1, t2 = min(theta_start, theta_end), max(theta_start, theta_end)
            
            mid_angle_deg = (t1 + t2) / 2
            mid_angle_rad = np.deg2rad(mid_angle_deg)
            
            color = base_colors[i % len(base_colors)]

            # --- B. Height Calculation ---
            normalized_height = value / max_value
            current_rim_r = inner_void_r + (max_rim_r - inner_void_r) * normalized_height
            # Ensure minimum visibility
            if current_rim_r < inner_void_r + 0.1: 
                current_rim_r = inner_void_r + 0.1
                
            wedge_width = current_rim_r - inner_void_r

            # --- LAYER 1: Shadow ---
            shadow_offset_x = 0.02
            shadow_offset_y = -0.02
            shadow = patches.Wedge(
                center=(shadow_offset_x, shadow_offset_y),
                r=current_rim_r,
                theta1=t1,
                theta2=t2,
                width=wedge_width,
                facecolor='gray',
                alpha=0.3,
                edgecolor=None
            )
            ax.add_patch(shadow)

            # --- MAIN WEDGE ---
            full_wedge = patches.Wedge(
                center=(0, 0),
                r=current_rim_r,
                theta1=t1,
                theta2=t2,
                width=wedge_width,
                facecolor=color,
                edgecolor='white',
                linewidth=1.5
            )
            ax.add_patch(full_wedge)

            # --- VALUE LABELS (Inside Wedge) ---
            # Position text slightly inside the outer edge
            label_r = current_rim_r - 0.15 
            if label_r < inner_void_r: label_r = inner_void_r + 0.05
            
            x_text = label_r * np.cos(mid_angle_rad)
            y_text = label_r * np.sin(mid_angle_rad)

            ax.text(x_text, y_text, f"{int(value)}%", 
                    ha='center', va='center', 
                    fontsize=12, fontweight='bold', color='white')

            # --- CATEGORY LABELS (Outside Wedge) ---
            # To ensure the label is readable, place it outside the max rim
            cat_label_r = current_rim_r + 0.15
            x_label = cat_label_r * np.cos(mid_angle_rad)
            y_label = cat_label_r * np.sin(mid_angle_rad)

            # Smart Alignment based on angle
            ha = 'center'
            # Normalize angle to 0-360
            norm_angle = mid_angle_deg % 360
            if 0 <= norm_angle < 90 or 270 <= norm_angle < 360:
                ha = 'left' if x_label > 0 else 'right'
            else:
                ha = 'right' if x_label < 0 else 'left'

            # Just center it for circular logic usually works best if distance is enough
            ax.text(x_label, y_label, label, 
                    ha='center', va='center', 
                    fontsize=10, fontweight='bold', color='#333333')

        return ChartFactory._to_base64(fig)

    @staticmethod
    def generate_vark_circles(scores, labels, descriptions=None):
        """
        Generates the VARK circle chart.
        Args:
            scores: List of scores.
            labels: List of labels.
            descriptions: (Optional) List of 4 strings generated by LLM. 
                          Order MUST be [Visual, Auditory, Read/Write, Kinesthetic].
                          If None, defaults to static definitions.
        """
        # 1. Setup White Background
        bg_color = 'white'
        fig, ax = plt.subplots(figsize=(8, 8))
        
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        ax.set_xlim(-2.05, 2.05)
        ax.set_ylim(-2.05, 2.05)
        ax.set_aspect('equal')
        ax.axis('off')

        radius = 1.0 
        
        # 2. Handle Descriptions (LLM vs Static Fallback)
        default_descs = [
            'Visual learners prefer information presented in a visual format like graphs, charts, or diagrams.',
            'Auditory learners learn best through listening and verbal instructions.',
            'Reading/Writing learners excel when information is presented in written form, such as reading textbooks.',
            'Kinesthetic learners learn by doing and prefer hands-on activities or practical experiences.'
        ]
        
        # Ensure we have exactly 4 descriptions, otherwise fallback to defaults
        if descriptions and len(descriptions) == 4:
            final_descs = descriptions
        else:
            final_descs = default_descs

        # 3. Define VARK Data with Dynamic Descriptions
        vark_data = [
            {
                'letter': 'V', 'title': 'Visual', 'color': '#FFF1A8', 
                'center': (-1, 1), 'highlight_angle': (90, 180), 
                'desc': final_descs[0]
            },
            {
                'letter': 'A', 'title': 'Auditory', 'color': '#C8F0A8', 
                'center': (1, 1), 'highlight_angle': (0, 90), 
                'desc': final_descs[1]
            },
            {
                'letter': 'R', 'title': 'Reading / Writing', 'color': '#8CCAF2', 
                'center': (-1, -1), 'highlight_angle': (180, 270), 
                'desc': final_descs[2]
            },
            {
                'letter': 'K', 'title': 'Kinesthetic', 'color': '#D69EF5', 
                'center': (1, -1), 'highlight_angle': (270, 360), 
                'desc': final_descs[3]
            }
        ]

        # 4. Render Circles
        for item in vark_data:
            cx, cy = item['center']
            
            # Circle Background
            circle = patches.Circle((cx, cy), radius, facecolor=item['color'], edgecolor='none', zorder=1)
            ax.add_patch(circle)
            
            # Arcs (Darker color for visibility on white bg)
            start_ang, end_ang = item['highlight_angle']
            arc = patches.Arc((cx, cy), width=radius*2.05, height=radius*2.05, angle=0, theta1=start_ang, theta2=end_ang, color='black', linewidth=3, alpha=0.8, zorder=2, capstyle='round')
            ax.add_patch(arc)
            arc2 = patches.Arc((cx, cy), width=radius*2.02, height=radius*2.02, angle=0, theta1=start_ang+5, theta2=end_ang-5, color='black', linewidth=1, alpha=0.5, zorder=2)
            ax.add_patch(arc2)

            # Labels (Dark Text)
            ax.text(cx, cy + 0.4, item['letter'], ha='center', va='center', fontsize=65, fontweight='bold', color='#333333', zorder=3)
            ax.text(cx, cy - 0.1, item['title'], ha='center', va='center', fontsize=11, fontweight='bold', color='#333333', zorder=3)
            
            # Separator Line REMOVED here as requested

            # Dynamic Description Text (Text Wrap)
            wrapped_desc = textwrap.fill(item['desc'], width=28)
            ax.text(cx, cy - 0.5, wrapped_desc, ha='center', va='center', fontsize=7, color='#333333', zorder=3, linespacing=1.3)

        return ChartFactory._to_base64(fig)

    @staticmethod
    def generate_gauge(value, min_val=0, max_val=100):
        bg_color = "white"
        c_red = "#e84e1b"
        c_yellow = "#f2c037"
        c_l_green = "#5cb85c"
        c_d_green = "#369b46"
        c_needle = "#1a1a1a"

        fig, ax = plt.subplots(figsize=(6, 5), facecolor=bg_color)
        ax.set_facecolor(bg_color)

        sizes = [67.5, 67.5, 67.5, 67.5, 90] 
        colors = [c_d_green, c_l_green, c_yellow, c_red, bg_color]
        
        wedges, _ = ax.pie(
            sizes, 
            colors=colors, 
            startangle=-45, 
            counterclock=True, 
            radius=1.0,
            wedgeprops={'width': 0.35, 'edgecolor': bg_color, 'linewidth': 4} 
        )

        total_span = 270
        start_angle = 225
        angle_deg = start_angle - (total_span * (value - min_val) / (max_val - min_val))
        angle_rad = np.deg2rad(angle_deg)
        
        needle_length = 0.55
        needle_width = 0.08
        
        x_tip = needle_length * np.cos(angle_rad)
        y_tip = needle_length * np.sin(angle_rad)
        x_base_l = needle_width * np.cos(angle_rad + np.pi/2)
        y_base_l = needle_width * np.sin(angle_rad + np.pi/2)
        x_base_r = needle_width * np.cos(angle_rad - np.pi/2)
        y_base_r = needle_width * np.sin(angle_rad - np.pi/2)
        
        needle_poly = patches.Polygon(
            [[x_tip, y_tip], [x_base_l, y_base_l], [x_base_r, y_base_r]], 
            closed=True, color=c_needle, zorder=10
        )
        ax.add_patch(needle_poly)
        ax.add_patch(plt.Circle((0, 0), needle_width, color=c_needle, zorder=11))

        ax.text(0, -0.65, f"{value}", ha='center', va='center', fontsize=45, fontweight='bold', color='black')
        ax.text(0, -0.85, "NPS", ha='center', va='center', fontsize=16, fontweight='bold', color='black')

        ax.set_aspect('equal')
        plt.axis('off')
        
        return ChartFactory._to_base64(fig)