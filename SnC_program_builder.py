import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px


TRAINING_BLOCKS = {
    'Strength': {
        'duration_weeks': 6,
        'residual_weeks': 5,
        'intensity_range': (85, 100),
        'subblocks': [
            {
                'name': 'Eccentric',
                'weeks': 2,
                'training_structure': {
                    'main_exercises': [
                        'Back Squat',
                        'Sport Squat',
                        'Deadlift (Trap Bar)',
                        'Bench Press',
                        'DB Shoulder Press',
                        'Rows'
                    ],
                    'weekly_structure': {
                        'Monday': {
                            'type': 'Medium Intensity',
                            'intensity_range': (82, 87),
                            'tempo': {
                                'eccentric': 6,
                                'isometric': 0,
                                'concentric': 0  # X represents explosive
                            },
                            'sets': '2-4',
                            'reps': '1-3',
                            'french_contrast': {
                                'sequence': [
                                    'Main Compound Exercise',
                                    'Plyometric Exercise',
                                    'Weighted/Accelerated Plyometric'
                                ]
                            }
                        },
                        'Wednesday': {
                            'type': 'High Intensity',
                            'intensity_range': (90, 95),
                            'tempo': {
                                'eccentric': 0,
                                'isometric': 0,
                                'concentric': 0
                            },
                            'note': 'Reactive day - focus on explosive concentric phase'
                        },
                        'Friday': {
                            'type': 'High Volume',
                            'intensity_range': (75, 80),
                            'tempo': {
                                'eccentric': 5,
                                'isometric': 0,
                                'concentric': 0
                            },
                            'french_contrast': {
                                'sequence': [
                                    'Main Compound Exercise',
                                    'Plyometric Exercise',
                                    'Weighted/Accelerated Plyometric'
                                ]
                            }
                        }
                    }
                }
            },
            {
                'name': 'Isometric',
                'weeks': 2,
                'training_structure': {
                    'main_exercises': [
                        'Back Squat',
                        'Sport Squat',
                        'Deadlift (Trap Bar)',
                        'Bench Press',
                        'DB Shoulder Press',
                        'Rows'
                    ],
                    'weekly_structure': {
                        'Monday': {
                            'type': 'Medium Intensity',
                            'intensity_range': (82, 87),
                            'tempo': {
                                'eccentric': 0,
                                'isometric': 3,
                                'concentric': 0
                            },
                            'sets': '3-5',
                            'reps': '2-3',
                            'french_contrast': {
                                'sequence': [
                                    'Main Compound Exercise',
                                    'Plyometric Exercise',
                                    'Weighted/Accelerated Plyometric'
                                ]
                            }
                        },
                        'Wednesday': {
                            'type': 'High Intensity',
                            'intensity_range': (90, 95),
                            'tempo': {
                                'eccentric': 0,
                                'isometric': 0,
                                'concentric': 0
                            },
                            'note': 'Reactive day - focus on explosive movement'
                        },
                        'Friday': {
                            'type': 'High Volume',
                            'intensity_range': (75, 80),
                            'tempo': {
                                'eccentric': 3,
                                'isometric': 2,
                                'concentric': 0
                            },
                            'french_contrast': {
                                'sequence': [
                                    'Main Compound Exercise',
                                    'Plyometric Exercise',
                                    'Weighted/Accelerated Plyometric'
                                ]
                            }
                        }
                    }
                }
            },
            {
                'name': 'Concentric',
                'weeks': 2,
                'training_structure': {
                    'main_exercises': [
                        'Back Squat',
                        'Sport Squat',
                        'Deadlift (Trap Bar)',
                        'Bench Press',
                        'DB Shoulder Press',
                        'Rows'
                    ],
                    'weekly_structure': {
                        'Monday': {
                            'type': 'Medium Intensity',
                            'intensity_range': (82, 87),
                            'tempo': {
                                'eccentric': 0,
                                'isometric': 0,
                                'concentric': 0
                            },
                            'sets': '3-4',
                            'reps': '2-3',
                            'french_contrast': {
                                'sequence': [
                                    'Main Compound Exercise',
                                    'Plyometric Exercise',
                                    'Weighted/Accelerated Plyometric'
                                ]
                            }
                        },
                        'Wednesday': {
                            'type': 'High Intensity',
                            'intensity_range': (90, 95),
                            'tempo': {
                                'eccentric': 0,
                                'isometric': 0,
                                'concentric': 0
                            },
                            'note': 'Max power day - focus on explosive movement'
                        },
                        'Friday': {
                            'type': 'High Volume',
                            'intensity_range': (75, 80),
                            'tempo': {
                                'eccentric': 0,
                                'isometric': 0,
                                'concentric': 0
                            },
                            'french_contrast': {
                                'sequence': [
                                    'Main Compound Exercise',
                                    'Plyometric Exercise',
                                    'Weighted/Accelerated Plyometric'
                                ]
                            }
                        }
                    }
                }
            }
        ]
    },
    'Power': {
        'duration_weeks': 4,
        'residual_weeks': 3,
        'intensity_range': (55, 80),
        'training_structure': {
            'main_exercises': [
                'Clean Pull',
                'Power Clean',
                'Snatch Pull',
                'Power Snatch',
                'Jump Squats'
            ],
            'weekly_structure': {
                'Monday': {
                    'type': 'Technique Focus',
                    'intensity_range': (55, 65),
                    'sets': '4-6',
                    'reps': '3-5',
                    'note': 'Focus on perfect technique and bar path'
                },
                'Wednesday': {
                    'type': 'Power Development',
                    'intensity_range': (70, 80),
                    'sets': '4-5',
                    'reps': '2-3',
                    'note': 'Focus on bar speed and power output'
                },
                'Friday': {
                    'type': 'Complex Training',
                    'intensity_range': (60, 70),
                    'sets': '3-4',
                    'reps': '2-3',
                    'complex': {
                        'sequence': [
                            'Olympic Lift',
                            'Plyometric Movement',
                            'Speed-Strength Exercise'
                        ]
                    }
                }
            }
        }
    },
    'Speed': {
        'duration_weeks': 4,
        'residual_weeks': 2,
        'intensity_range': (30, 55),
        'training_structure': {
            'main_exercises': [
                'Sprint Variations',
                'Plyometrics',
                'Medicine Ball Throws',
                'Band-Resisted Movements'
            ],
            'weekly_structure': {
                'Monday': {
                    'type': 'Linear Speed',
                    'intensity_range': (95, 100),  # % of max speed
                    'volume': '4-6 sets of 20-30m',
                    'rest': '2-3 min between sets'
                },
                'Wednesday': {
                    'type': 'Multidirectional Speed',
                    'intensity_range': (90, 95),
                    'volume': '6-8 sets of varied drills',
                    'rest': '90-120 sec between sets'
                },
                'Friday': {
                    'type': 'Speed-Strength',
                    'intensity_range': (30, 50),  # % of 1RM for weighted exercises
                    'volume': '4-5 sets per exercise',
                    'complex': {
                        'sequence': [
                            'Light Weight Exercise',
                            'Sprint or Agility Drill',
                            'Reactive Movement'
                        ]
                    }
                }
            }
        }
    },
    'Hypertrophy': {
        'duration_weeks': 4,
        'residual_weeks': 2,
        'intensity_range': (65, 75),
        'training_structure': {
            'main_exercises': [
                'Compound Movements',
                'Isolation Exercises',
                'Accessory Work'
            ],
            'weekly_structure': {
                'Monday': {
                    'type': 'Push Focus',
                    'intensity_range': (65, 75),
                    'sets': '3-4',
                    'reps': '8-12',
                    'tempo': '2-0-2'  # eccentric-isometric-concentric
                },
                'Wednesday': {
                    'type': 'Pull Focus',
                    'intensity_range': (65, 75),
                    'sets': '3-4',
                    'reps': '8-12',
                    'tempo': '2-0-2'
                },
                'Friday': {
                    'type': 'Full Body',
                    'intensity_range': (65, 75),
                    'sets': '3-4',
                    'reps': '8-12',
                    'tempo': '2-0-2',
                    'note': 'Super-sets and tri-sets incorporated'
                }
            }
        }
    }
}

def main():
    st.title('Strength & Conditioning Program Builder')
    
    # Sidebar for program settings
    st.sidebar.header('Program Settings')
    training_days = st.sidebar.selectbox('Training Days per Week', [3, 4, 5])
    
    # Main area for block arrangement
    st.header('Arrange Your Training Blocks')
    
    # Initialize session state for storing blocks if not exists
    if 'program_blocks' not in st.session_state:
        st.session_state.program_blocks = []
    
    # Display available blocks for selection
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader('Available Blocks')
        selected_block = st.selectbox('Select a block to add:', list(TRAINING_BLOCKS.keys()))
        if st.button('Add Block'):
            st.session_state.program_blocks.append(selected_block)
    
    with col2:
        st.subheader('Your Program')
        for i, block in enumerate(st.session_state.program_blocks):
            col = st.columns(2)
            with col[0]:
                st.write(f"{i+1}. {block}")
            with col[1]:
                if st.button('Remove', key=f'remove_{i}'):
                    st.session_state.program_blocks.pop(i)
                    st.experimental_rerun()
    
    # Display program analysis
    if st.session_state.program_blocks:
        analyze_program(st.session_state.program_blocks, training_days)

def create_residual_effects_plot(blocks):
    """Create a plot showing residual training effects over the program duration"""
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
    
    # Mini-block recommendations (in weeks from start of block)
    MINI_BLOCK_RECOMMENDATIONS = {
        'Maximal Strength': 4,  # Recommend mini-block every 4 weeks
        'Power': 3,
        'Speed': 2,
        'Hypertrophy': 3
    }
    
    timeline = []
    effects_data = {ability: [] for ability in RESIDUAL_EFFECTS.keys()}
    mini_block_markers = []
    current_week = 0
    
    # Calculate total program duration including peak week
    total_weeks = sum(TRAINING_BLOCKS[block]['duration_weeks'] for block in blocks) + 1  # +1 for peak week
    
    for week in range(total_weeks + max(RESIDUAL_EFFECTS.values())//7):
        timeline.append(week)
        week_effects = {ability: 0 for ability in RESIDUAL_EFFECTS.keys()}
        
        # Calculate effect from each block
        current_position = 0
        for block_idx, block in enumerate(blocks):
            block_duration = TRAINING_BLOCKS[block]['duration_weeks']
            block_end_week = current_position + block_duration
            ability = BLOCK_TO_ABILITY[block]
            
            # If the week is within the block duration or residual period
            if week >= current_position:
                days_since_block = (week - block_end_week) * 7
                
                if week < block_end_week:
                    # During block training
                    week_effects[ability] = 100
                    
                    # Check for mini-block recommendations
                    weeks_into_block = week - current_position
                    if weeks_into_block > 0 and weeks_into_block % MINI_BLOCK_RECOMMENDATIONS[ability] == 0:
                        mini_block_markers.append({
                            'week': week,
                            'ability': ability,
                            'type': 'mini'
                        })
                        
                elif days_since_block < RESIDUAL_EFFECTS[ability]:
                    # During residual period
                    residual_effect = 100 * (1 - days_since_block/RESIDUAL_EFFECTS[ability])
                    week_effects[ability] = max(0, residual_effect)
            
            current_position += block_duration
            
        # Add peak week effect
        if week == total_weeks - 1:  # Last week of regular program
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
    
    # Plot main effects lines
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
    
    # Add mini-block markers
    for marker in mini_block_markers:
        fig.add_annotation(
            x=marker['week'],
            y=100,
            text="↑",
            showarrow=False,
            font=dict(size=20, color=colors[marker['ability']]),
            yshift=10
        )
    
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
        title='Residual Training Effects Over Program Duration',
        xaxis_title='Weeks',
        yaxis_title='Effect Retention (%)',
        hovermode='x unified',
        showlegend=True,
        yaxis_range=[0, 100],
        annotations=[
            dict(
                x=current_week,
                y=100,
                xref="x",
                yref="y",
                text="Program End",
                showarrow=True,
                arrowhead=2,
                ax=0,
                ay=-40
            )
        ]
    )
    
    # Add recommendations to Streamlit
    st.write("### Training Block Recommendations")
    st.write("To optimize the training effect retention:")
    for ability in RESIDUAL_EFFECTS.keys():
        st.write(f"- Include {ability} mini-blocks every {MINI_BLOCK_RECOMMENDATIONS[ability]} weeks to maintain adaptations")
    st.write("- The peak week at the end helps to maximize all training effects for competition")
    st.write("- Arrows (↑) on the graph indicate recommended mini-block insertion points")
    
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
    
    # Track active mini-blocks and their effects
    active_mini_blocks = []
    
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

    
# Define weekly training schedules based on number of training days
#WEEKLY_SCHEDULES = {
#    3: ['Monday', 'Wednesday', 'Friday'],
#    4: ['Monday', 'Tuesday', 'Thursday', 'Friday'],
#    5: ['Monday', 'Tuesday', 'Wednesday', 'Friday', 'Saturday'],
#    6: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
#}

def generate_weekly_schedule(training_days):
    """Generate a weekly training schedule based on number of training days"""
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


def create_intensity_plot(blocks):
    """Create a line plot showing intensity ranges over the program duration"""
    weeks = []
    intensities_min = []
    intensities_max = []
    block_labels = []
    current_week = 0
    
    for block in blocks:
        block_data = TRAINING_BLOCKS[block]
        duration = block_data['duration_weeks']
        
        for week in range(duration):
            weeks.append(current_week + week)
            intensities_min.append(block_data['intensity_range'][0])
            intensities_max.append(block_data['intensity_range'][1])
            block_labels.append(block)
        
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

def display_training_structure(block_name, subblock_name=None):
    """Display the detailed training structure for a block/subblock"""
    block_data = TRAINING_BLOCKS[block_name]
    
    if subblock_name and block_data['subblocks']:
        subblock = next((sb for sb in block_data['subblocks'] if sb['name'] == subblock_name), None)
        if subblock and 'training_structure' in subblock:
            st.subheader(f"{block_name} - {subblock_name} Training Structure")
            
            # Display main exercises
            st.write("**Main Exercises:**")
            for ex in subblock['training_structure']['main_exercises']:
                st.write(f"- {ex}")
            
            # Display weekly structure
            st.write("\n**Weekly Structure:**")
            for day, details in subblock['training_structure']['weekly_structure'].items():
                st.write(f"\n***{day}*** - {details['type']}")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"Intensity: {details['intensity_range'][0]}-{details['intensity_range'][1]}%")
                    if 'sets' in details:
                        st.write(f"Sets: {details['sets']}")
                    if 'reps' in details:
                        st.write(f"Reps: {details['reps']}")
                
                with col2:
                    st.write("Tempo:")
                    st.write(f"- Eccentric: {details['tempo']['eccentric']}s")
                    st.write(f"- Isometric: {details['tempo']['isometric']}s")
                    st.write(f"- Concentric: {details['tempo']['concentric']}")
                
                if 'french_contrast' in details:
                    st.write("\nFrench Contrast Sequence:")
                    for step in details['french_contrast']['sequence']:
                        st.write(f"1. {step}")
                
                if 'note' in details:
                    st.info(details['note'])

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

def create_block_distribution_plot(blocks):
    """Create a pie chart showing the distribution of training blocks"""
    block_counts = pd.Series(blocks).value_counts()
    
    fig = px.pie(
        values=block_counts.values,
        names=block_counts.index,
        title='Training Block Distribution'
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig

def create_schedule_heatmap(schedule_df):
    """Create a heatmap visualization of the weekly schedule"""
    # Create intensity values for heatmap
    intensity_map = {
        'High Intensity': 3,
        'Medium-High Intensity': 2,
        'Medium Intensity': 1,
        'High Volume': 2.5
    }
    
    intensity_values = [[intensity_map[training] for training in schedule_df['Training']]]  # Wrap in another list
    
    fig = go.Figure(data=go.Heatmap(
        z=intensity_values,  # Now properly formatted as 2D array
        x=schedule_df['Day'].tolist(),
        y=['Training'],
        colorscale='Viridis',
        showscale=False,
        text=[schedule_df['Training'].tolist()],  # Convert to list
        texttemplate="%{text}",
        textfont={"size": 12, "color": "white"}  # Changed from textcolor to textfont
    ))
    
    fig.update_layout(
        title='Weekly Training Schedule Intensity',
        xaxis_title='Day of Week',
        yaxis_title='',
        height=200
    )
    
    return fig

def generate_weekly_schedule(training_days):
    schedule = WEEKLY_SCHEDULES[training_days]
    intensities = {
        'Monday': 'Medium Intensity',
        'Wednesday': 'High Intensity',
        'Friday': 'High Volume'
    }
    
    schedule_data = []
    for day in schedule:
        intensity = intensities.get(day, 'Medium-High Intensity')
        schedule_data.append({'Day': day, 'Training': intensity})
    
    return pd.DataFrame(schedule_data)

if __name__ == "__main__":
    main()
