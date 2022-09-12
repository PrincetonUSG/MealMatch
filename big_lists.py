
"""List of large size that we've moved to an external file."""

dhall_list = sorted(["CJL", "Forbes", "NCW/Yeh", "RoMa", "Whitman"])


mjr = ['African American Studies', 'Anthropology', 'Architecture',
       'Art and Archaeology', 'Astrophysical Sciences',
       'Chemical and Biological Engineering', 'Chemistry',
       'Civil and Environmental Engineering', 'Classics',
       'Comparative Literature', 'Computer Science',
       'East Asian Studies', 'Ecology and Evolutionary Biology',
       'Economics', 'Electrical and Computer Engineering',
       'English', 'French and Italian', 'Geosciences',
       'German', 'History', 'Mathematics',
       'Mechanical and Aerospace Engineering',
       'Molecular Biology', 'Music',
       'Near Eastern Studies', 'Neuroscience',
       'Operations Research and Financial Engineering',
       'Philosophy', 'Physics', 'Politics',
       'Psychology', 'Religion',
       'School of Public and International Affairs',
       'Slavic Languages and Literatures',
       'Sociology', 'Spanish and Portuguese',
       'Atmospheric and Oceanic Sciences',
       'Applied and Computational Mathematics',
       'Musicology', 'Music Composition',
       'Population Studies', 'Plasma Physics',
       'Quantitative and Computational Biology',
       'History of Science', 'Independent Study', 'Other']
dc = [
    'AAS', 'ANT', 'ARC', 'ART', 'AST', 'CBE',
    'CHM', 'CEE', 'CLA', 'COM', 'COS',
    'EAS', 'EEB', 'ECO', 'ECE', 'ENG',
    'FRE/ITA', 'GEO', 'GER', 'HIS', 'MAT', 'MAE',
    'MOL', 'MUS', 'NES', 'NEU', 'ORFE',
    'PHI', 'PHY', 'POL', 'PSY', 'REL',
    'SPIA', 'SLA', 'SOC', 'SPA/POR',
    'AOS', 'ACM', 'MUS', 'MUS',
    'POP', 'PHY', 'QCB', 'HOS']
majors = sorted(mjr)
dept_code = dict(zip(mjr, dc))
