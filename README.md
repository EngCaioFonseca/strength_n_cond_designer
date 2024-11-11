# Strength & Conditioning Program Builder

A Python-based application that helps strength and conditioning coaches design, visualize, and optimize training programs using block periodization principles.
ref: Tripashic Training by Cal Dietz

## Features

- **Block Periodization Design**: Create training programs using different training blocks:
  - Strength
  - Power
  - Speed
  - Hypertrophy

- **Program Analysis**:
  - Training intensity profiles
  - Residual training effects visualization
  - Optimized mini-block recommendations
  - Weekly schedule generation
  - Program timeline visualization

- **Optimization Tools**:
  - Mini-block implementation suggestions
  - Peak week planning
  - Training load distribution
  - Recovery considerations

## Installation

1. Clone the repository:

bash

git clone https://github.com/EngCaioFonseca/strength_n_cond_designer.git

cd strength_n_cond_designer

2. Install required packages:

bash

pip install -r requirements.txt

3. Run the application:

bash

streamlit run SnC_program_builder.py


## Dependencies

- Python 3.8+
- Streamlit
- Plotly
- Pandas
- NumPy

## Usage

1. Select the number of training days per week
2. Choose your training blocks in sequence
3. Analyze the generated program, including:
   - Intensity distribution
   - Residual effects
   - Block analysis
   - Weekly schedule
   - Program timeline

## Program Components

### Training Blocks
- **Strength Block**: Focus on maximal force production
- **Power Block**: Emphasis on rate of force development
- **Speed Block**: Maximum velocity development
- **Hypertrophy Block**: Muscle mass development

### Mini-Blocks
Maintenance blocks designed to retain adaptations from previous training phases:
- Strength maintenance: 2-3 sets at 80-85% 1RM
- Power maintenance: Explosive movements at 60-70% 1RM
- Speed maintenance: Short sprints and plyometrics
- Hypertrophy maintenance: 2-3 sets of main exercises

### Peak Week
Optimized final week to maximize performance for competition:
- Reduced volume
- Maintained intensity
- Integration of all training qualities

## Visualizations

1. **Intensity Profile**:
   - Shows training intensity distribution over time
   - Displays min/max intensity ranges
   - Block transition markers

2. **Residual Effects**:
   - Original training effects
   - Optimized effects with mini-blocks
   - Peak week integration

3. **Program Timeline**:
   - Gantt chart of training blocks
   - Mini-block placement
   - Peak week timing

4. **Weekly Schedule**:
   - Training day distribution
   - Intensity allocation
   - Recovery periods

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

- Based on block periodization principles
- Incorporates residual training effects research
- Optimized for strength and conditioning applications

## Contact

Caio Fonseca - engcaiofonseca@protonmail.com

Project Link: [https://github.com/EngCaioFonseca/strength_n_cond_designer](https://github.com/EngCaioFonseca/strength_n_cond_designer)

## Screenshots

![image](https://github.com/user-attachments/assets/965f56d6-6a6d-45a5-a3fc-f383c68ddd72)

![image](https://github.com/user-attachments/assets/1e0544a8-8b38-4524-884a-d3df6d10c875)

![image](https://github.com/user-attachments/assets/579a5366-b084-4516-9354-758c91c9556f)

![image](https://github.com/user-attachments/assets/4dcd364f-852d-4cd0-b495-b3e775b476b3)

![image](https://github.com/user-attachments/assets/c76705fd-b6e1-4c80-b6dc-14a121c257c5)

![image](https://github.com/user-attachments/assets/b1615518-53b4-4234-9178-d5952e30c833)

![image](https://github.com/user-attachments/assets/407dd04c-3c49-42bd-8a53-3c59be05e637)


## Future Improvements

- [ ] Add exercise library
- [ ] Include volume calculations
- [ ] Export program to PDF
- [ ] Add custom block creation
- [ ] Implement athlete profiles
- [ ] Add performance tracking
