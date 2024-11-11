import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Define constants for training blocks
TRAINING_BLOCKS = {
    'Strength': {'duration_weeks': 4, 'intensity_range': (75, 90)},
    'Power': {'duration_weeks': 3, 'intensity_range': (60, 80)},
    'Speed': {'duration_weeks': 2, 'intensity_range': (85, 100)},
    'Hypertrophy': {'duration_weeks': 5, 'intensity_range': (65, 75)}
}

def create_intensity_plot(blocks):
    """Create a line plot showing intensity ranges over the program duration"""
    weeks = []
    intensities_min = []
    intensities_max = []
    current_week = 0
    
    for block in blocks:
        block_data = TRAINING_BLOCKS[block]
        duration = block_data['duration_weeks']
        
        for week in range(duration):
            weeks.append(current_week + week)
            intensities_min.append(block_data['intensity_range'][0])
            intensities_max.append(block_data['intensity_range'][1])
        
        current_week += duration

    fig = go.Figure()
    
    # Add range area
    fig.add_trace(go.Scatter(
        x=weeks + weeks[::-1],
        y=intensities_max + intensities_min[::-1],
        fill='toself',
        fillcolor='rgba(0,100,80,0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        showlegend=False,
        name='Intensity Range'
    ))
    
    # Add lines for min and max intensity
    fig.add_trace(go.Scatter(
        x=weeks,
        y=intensities_max,
        line=dict(color='rgb(0,100,80)'),
        name='Max Intensity'
    ))
    
    fig.add_trace(go.Scatter(
        x=weeks,
        y=intensities_min,
        line=dict(color='rgb(0,100,80)', dash='dash'),
        name='Min Intensity'
    ))

    # Update layout
    fig.update_layout(
        title='Program Intensity Profile',
        xaxis_title='Week',
        yaxis_title='Intensity (%1RM)',
        hovermode='x unified',
        showlegend=True
    )
    
    return fig

def create_residual_effects_plot(blocks):
    """Create a plot showing residual training effects"""
    # Define residual effects in days for different abilities
    RESIDUAL_EFFECTS = {
        'Maximal Strength': 30,
        'Power': 18,
        'Speed': 5,
        'Hypertrophy': 15
    }
    
    # Map block names to their corresponding training effects
    BLOCK_TO_ABILITY = {
        'Strength': 'Maximal Strength',
        'Power': 'Power',
        'Speed': 'Speed',
        'Hypertrophy': 'Hypertrophy'
    }
    
    timeline = []
    effects_data = {ability: [] for ability in RESIDUAL_EFFECTS.keys()}
    current_week = 0
    
    # Calculate total program duration including peak week
    total_weeks = sum(TRAINING_BLOCKS[block]['duration_weeks'] for block in blocks) + 1
    
    for week in range(total_weeks + max(RESIDUAL_EFFECTS.values())//7):
        timeline.append(week)
        week_effects = {ability: 0 for ability in RESIDUAL_EFFECTS.keys()}
        
        # Calculate effect from each block
        current_position = 0
        for block_idx, block in enumerate(blocks):
            block_duration = TRAINING_BLOCKS[block]['duration_weeks']
            block_end_week = current_position + block_duration
            ability = BLOCK_TO_ABILITY[block]
            
            if week >= current_position:
                days_since_block = (week - block_end_week) * 7
                
                if week < block_end_week:
                    # During block training
                    week_effects[ability] = 100
                    
                elif days_since_block < RESIDUAL_EFFECTS[ability]:
                    # During residual period
                    base_residual = 100 * (1 - days_since_block/RESIDUAL_EFFECTS[ability])
                    week_effects[ability] = max(base_residual, week_effects[ability])
            
            current_position += block_duration
            
        # Add peak week effect
        if week == total_weeks - 1:
            for ability in RESIDUAL_EFFECTS.keys():
                week_effects[ability] = 100
        
        # Add effects to data
        for ability in RESIDUAL_EFFECTS.keys():
            effects_data[ability].append(week_effects[ability])
    
    # Create plot
    fig = go.Figure()
    
    colors = {
        'Maximal Strength': 'rgb(31, 119, 180)',
        'Power': 'rgb(255, 127, 14)',
        'Speed': 'rgb(44, 160, 44)',
        'Hypertrophy': 'rgb(214, 39, 40)'
    }
    
    for ability in RESIDUAL_EFFECTS.keys():
        fig.add_trace(go.Scatter(
            x=timeline,
            y=effects_data[ability],
            name=ability,
            line=dict(color=colors[ability]),
            hovertemplate="Week %{x}<br>" +
                         f"{ability}: %{{y:.1f}}%<br>" +
                         "<extra></extra>"
        ))
    
    # Add block transition lines
    current_week = 0
    for i, block in enumerate(blocks):
        if i > 0:
            fig.add_vline(
                x=current_week,
                line_dash="dash",
                line_color="gray",
                opacity=0.5
            )
        current_week += TRAINING_BLOCKS[block]['duration_weeks']
    
    # Add peak week marker
    fig.add_vrect(
        x0=total_weeks-1,
        x1=total_weeks,
        fillcolor="rgba(255, 255, 0, 0.3)",
        layer="below",
        line_width=0,
        annotation_text="Peak Week",
        annotation_position="top left"
    )
    
    fig.update_layout(
        title='Residual Training Effects',
        xaxis_title='Weeks',
        yaxis_title='Effect Retention (%)',
        hovermode='x unified',
        showlegend=True,
        yaxis_range=[0, 100]
    )
    
    return fig

def create_optimized_residual_effects_plot(blocks):
    """Create a plot showing optimized residual training effects with mini-blocks"""
    # Define residual effects in days for different abilities
    RESIDUAL_EFFECTS = {
        'Maximal Strength': 30,
        'Power': 18,
        'Speed': 5,
        'Hypertrophy': 15
    }
    
    # Map block names to their corresponding training effects
    BLOCK_TO_ABILITY = {
        'Strength': 'Maximal Strength',
        'Power': 'Power',
        'Speed': 'Speed',
        'Hypertrophy': 'Hypertrophy'
    }
    
    # Mini-block effect on residual maintenance (percentage maintained)
    MINI_BLOCK_EFFECT = {
        'Maximal Strength': 0.8,  # Maintains 80% of original effect
        'Power': 0.75,
        'Speed': 0.7,
        'Hypertrophy': 0.75
    }
    
    timeline = []
    effects_data = {ability: [] for ability in RESIDUAL_EFFECTS.keys()}
    current_week = 0
    
    # Calculate total program duration including peak week
    total_weeks = sum(TRAINING_BLOCKS[block]['duration_weeks'] for block in blocks) + 1
    
    for week in range(total_weeks + max(RESIDUAL_EFFECTS.values())//7):
        timeline.append(week)
        week_effects = {ability: 0 for ability in RESIDUAL_EFFECTS.keys()}
        
        # Calculate effect from each block
        current_position = 0
        for block_idx, block in enumerate(blocks):
            block_duration = TRAINING_BLOCKS[block]['duration_weeks']
            block_end_week = current_position + block_duration
            ability = BLOCK_TO_ABILITY[block]
            
            if week >= current_position:
                days_since_block = (week - block_end_week) * 7
                
                if week < block_end_week:
                    # During block training
                    week_effects[ability] = 100
                    
                    # Add mini-blocks for previous abilities
                    if block_idx > 0:
                        for prev_block in blocks[:block_idx]:
                            prev_ability = BLOCK_TO_ABILITY[prev_block]
                            mini_block_effect = MINI_BLOCK_EFFECT[prev_ability] * 100
                            week_effects[prev_ability] = max(week_effects[prev_ability], mini_block_effect)
                            
                elif days_since_block < RESIDUAL_EFFECTS[ability]:
                    # During residual period with improved maintenance
                    base_residual = 100 * (1 - days_since_block/RESIDUAL_EFFECTS[ability])
                    mini_block_boost = 0
                    
                    # Check if there are subsequent blocks
                    if block_idx < len(blocks) - 1:
                        mini_block_boost = base_residual * MINI_BLOCK_EFFECT[ability]
                    
                    week_effects[ability] = max(base_residual + mini_block_boost, week_effects[ability])
            
            current_position += block_duration
            
        # Add peak week effect
        if week == total_weeks - 1:
            for ability in RESIDUAL_EFFECTS.keys():
                week_effects[ability] = 100
        
        # Add effects to data
        for ability in RESIDUAL_EFFECTS.keys():
            effects_data[ability].append(week_effects[ability])
    
    # Create plot
    fig = go.Figure()
    
    colors = {
        'Maximal Strength': 'rgb(31, 119, 180)',
        'Power': 'rgb(255, 127, 14)',
        'Speed': 'rgb(44, 160, 44)',
        'Hypertrophy': 'rgb(214, 39, 40)'
    }
    
    for ability in RESIDUAL_EFFECTS.keys():
        fig.add_trace(go.Scatter(
            x=timeline,
            y=effects_data[ability],
            name=ability,
            line=dict(color=colors[ability]),
            hovertemplate="Week %{x}<br>" +
                         f"{ability}: %{{y:.1f}}%<br>" +
                         "<extra></extra>"
        ))
    
    # Add block transition lines
    current_week = 0
    for i, block in enumerate(blocks):
        if i > 0:
            fig.add_vline(
                x=current_week,
                line_dash="dash",
                line_color="gray",
                opacity=0.5
            )
        current_week += TRAINING_BLOCKS[block]['duration_weeks']
    
    # Add peak week marker
    fig.add_vrect(
        x0=total_weeks-1,
        x1=total_weeks,
        fillcolor="rgba(255, 255, 0, 0.3)",
        layer="below",
        line_width=0,
        annotation_text="Peak Week",
        annotation_position="top left"
    )
    
    fig.update_layout(
        title='Optimized Residual Training Effects (with Mini-Blocks)',
        xaxis_title='Weeks',
        yaxis_title='Effect Retention (%)',
        hovermode='x unified',
        showlegend=True,
        yaxis_range=[0, 100]
    )
    
    return fig

def create_program_gantt(blocks):
    """Create a Gantt chart showing the full training program structure"""
    tasks = []
    current_week = 0
    
    # Colors for different block types
    colors = {
        'Strength': 'rgb(31, 119, 180)',
        'Power': 'rgb(255, 127, 14)',
        'Speed': 'rgb(44, 160, 44)',
        'Hypertrophy': 'rgb(214, 39, 40)',
        'Mini-Block': 'rgba(180, 180, 180, 0.7)',
        'Peak': 'rgb(255, 215, 0)'  # Gold color for peak week
    }
    
    # Add main training blocks and mini-blocks
    for i, block in enumerate(blocks):
        duration = TRAINING_BLOCKS[block]['duration_weeks']
        
        # Add main block
        tasks.append({
            'Task': f'{block} Block',
            'Start': current_week,
            'Duration': duration,
            'Color': colors[block],
            'Type': 'Main'
        })
        
        # Add mini-blocks for previous abilities if not the first block
        if i > 0:
            prev_block = blocks[i-1]
            # Add mini-blocks every 2 weeks
            for mini_week in range(current_week, current_week + duration, 2):
                tasks.append({
                    'Task': f'{prev_block} Mini-Block',
                    'Start': mini_week,
                    'Duration': 1,
                    'Color': colors['Mini-Block'],
                    'Type': 'Mini'
                })
        
        current_week += duration
    
    # Add peak week
    tasks.append({
        'Task': 'Peak Week',
        'Start': current_week,
        'Duration': 1,
        'Color': colors['Peak'],
        'Type': 'Peak'
    })
    
    # Create figure
    fig = go.Figure()
    
    # Add bars for each task
    for task in tasks:
        fig.add_trace(go.Bar(
            name=task['Task'],
            x=[task['Duration']],
            y=[task['Task']],
            orientation='h',
            marker=dict(color=task['Color']),
            base=task['Start'],
            showlegend=task['Type'] == 'Main',  # Only show main blocks in legend
            hovertemplate=(
                "Block: %{y}<br>" +
                "Start Week: %{base}<br>" +
                "Duration: %{x} week(s)<br>" +
                "<extra></extra>"
            )
        ))
    
    # Update layout
    fig.update_layout(
        title='Training Program Timeline',
        xaxis_title='Weeks',
        yaxis=dict(
            title='',
            autorange='reversed'  # Reverse y-axis to show tasks from top to bottom
        ),
        barmode='overlay',
        height=400,
        showlegend=True,
        legend_title='Training Blocks',
        hovermode='closest'
    )
    
    return fig

def generate_weekly_schedule(training_days):
    """Generate a weekly training schedule based on number of training days"""
    WEEKLY_SCHEDULES = {
        3: ['Monday', 'Wednesday', 'Friday'],
        4: ['Monday', 'Tuesday', 'Thursday', 'Friday'],
        5: ['Monday', 'Tuesday', 'Wednesday', 'Friday', 'Saturday'],
        6: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    }
    
    schedule = WEEKLY_SCHEDULES[training_days]
    intensities = {
        'Monday': 'High Intensity',
        'Tuesday': 'Medium-High Intensity',
        'Wednesday': 'Medium Intensity',
        'Thursday': 'Medium-High Intensity',
        'Friday': 'High Volume',
        'Saturday': 'Medium Intensity'
    }
    
    schedule_data = []
    for day in schedule:
        intensity = intensities.get(day, 'Medium Intensity')
        schedule_data.append({'Day': day, 'Training': intensity})
    
    return pd.DataFrame(schedule_data)

def create_schedule_heatmap(schedule_df):
    """Create a heatmap visualization of the weekly schedule"""
    intensity_map = {
        'High Intensity': 3,
        'Medium-High Intensity': 2,
        'Medium Intensity': 1,
        'High Volume': 2.5
    }
    
    intensity_values = [[intensity_map[training] for training in schedule_df['Training']]]
    
    fig = go.Figure(data=go.Heatmap(
        z=intensity_values,
        x=schedule_df['Day'].tolist(),
        y=['Training'],
        colorscale='Viridis',
        showscale=False,
        text=[schedule_df['Training'].tolist()],
        texttemplate="%{text}",
        textfont={"size": 12, "color": "white"}
    ))
    
    fig.update_layout(
        title='Weekly Training Schedule Intensity',
        xaxis_title='Day of Week',
        yaxis_title='',
        height=200
    )
    
    return fig

def analyze_program(blocks, training_days):
    """Analyze and visualize the training program structure"""
    st.title('Program Analysis')
    
    # Basic Program Info
    total_weeks = sum(TRAINING_BLOCKS[block]['duration_weeks'] for block in blocks)
    st.write(f"Program Duration: {total_weeks} weeks")
    
    # 1. Intensity Profile
    st.markdown("---")
    st.header("1. Intensity Profile")
    fig_intensity = create_intensity_plot(blocks)
    st.plotly_chart(fig_intensity, use_container_width=True)
    
    # 2. Residual Effects
    st.markdown("---")
    st.header("2. Residual Effects")
    fig_residuals = create_residual_effects_plot(blocks)
    st.plotly_chart(fig_residuals, use_container_width=True)
    
    # 3. Optimized Effects
    st.markdown("---")
    st.header("3. Optimized Effects")
    fig_optimized = create_optimized_residual_effects_plot(blocks)
    st.plotly_chart(fig_optimized, use_container_width=True)
    
    # 4. Block Analysis
    st.markdown("---")
    st.header("4. Block Analysis")
    
    for i, block in enumerate(blocks):
        st.subheader(f"Block {i+1}: {block}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Basic Information**")
            st.write(f"Duration: {TRAINING_BLOCKS[block]['duration_weeks']} weeks")
            st.write(f"Intensity: {TRAINING_BLOCKS[block]['intensity_range'][0]}-{TRAINING_BLOCKS[block]['intensity_range'][1]}%")
            
            st.markdown("**Main Exercises**")
            exercises = {
                'Strength': ['Back Squat', 'Sport Squat', 'Bench Press', 'DB Shoulder Press', 'Rows'],
                'Power': ['Clean', 'Snatch', 'Jump Squats', 'Medicine Ball Throws', 'Plyometrics'],
                'Speed': ['Sprint Variations', 'Plyometrics', 'Medicine Ball Throws', 'Band-Resisted Movements'],
                'Hypertrophy': ['Compound Movements', 'Isolation Exercises', 'Accessory Work']
            }
            for ex in exercises[block]:
                st.write(f"• {ex}")
        
        with col2:
            st.markdown("**Block Focus**")
            focus = {
                'Strength': ["Force production", "Progressive overload", "Neural adaptations"],
                'Power': ["Rate of force development", "Technical mastery", "Explosive strength"],
                'Speed': ["Maximum velocity", "Neural efficiency", "Minimal resistance"],
                'Hypertrophy': ["Muscle development", "Volume accumulation", "Metabolic stress"]
            }
            for point in focus[block]:
                st.write(f"• {point}")
        
        st.markdown("---")
    
    # 5. Weekly Schedule
    st.header("5. Weekly Schedule")
    try:
        schedule_df = generate_weekly_schedule(training_days)
        if not schedule_df.empty:
            fig_schedule = create_schedule_heatmap(schedule_df)
            st.plotly_chart(fig_schedule, use_container_width=True)
            
            st.markdown("**Training Guidelines**")
            st.write("• High Intensity: Technical focus")
            st.write("• Medium Intensity: Volume focus")
            st.write("• High Volume: Accumulation")
            
            st.markdown("**Recovery Focus**")
            st.write("• 24-48h between high intensity")
            st.write("• Active recovery on off days")
            st.write("• Sleep and nutrition priority")
    except Exception as e:
        st.warning(f"Schedule generation error: {str(e)}")
    
    # 6. Program Timeline
    st.markdown("---")
    st.header("6. Program Timeline")
    fig_gantt = create_program_gantt(blocks)
    st.plotly_chart(fig_gantt, use_container_width=True)
    
    # Implementation Guidelines
    st.markdown("---")
    st.markdown("### Implementation Guidelines")
    st.markdown("""
    1. Mini-blocks: 1-2 sessions per week
    2. Quality over quantity
    3. Adjust based on recovery
    4. Peak week: reduced volume, maintained intensity
    """)

# Main function to run the app
def main():
    st.sidebar.title("Program Builder")
    blocks = st.sidebar.multiselect(
        "Select Training Blocks",
        options=list(TRAINING_BLOCKS.keys()),
        default=list(TRAINING_BLOCKS.keys())
    )
    training_days = st.sidebar.slider("Training Days per Week", 3, 6, 4)
    
    if blocks:
        analyze_program(blocks, training_days)

if __name__ == "__main__":
    main()
