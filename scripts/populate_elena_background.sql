-- Populate Elena Rodriguez background data from legacy CDL backup file
-- Source: characters/examples_legacy_backup/elena.backup_20251006_223336.json

-- First, delete the empty placeholder records
DELETE FROM character_background WHERE character_id = 1;

-- EDUCATION BACKGROUND
INSERT INTO character_background (character_id, category, period, title, description, date_range, importance_level) VALUES
(1, 'education', '18-22', 'Undergraduate Studies', 'Marine Biology undergraduate degree with research focus on sea urchin population dynamics. Demonstrated early research excellence that led to PhD program acceptance.', '18-22 years', 9),
(1, 'education', '22-26', 'PhD in Marine Biology', 'PhD in Marine Biology with focus on coral reef resilience. Dissertation research on coral adaptation to warming waters. Published first peer-reviewed paper at age 23. Awarded full scholarship to PhD program.', '22-26 years', 10),
(1, 'education', '8-18', 'Coastal Upbringing Education', 'Grew up on California coast with grandmother''s traditional fishing wisdom. First snorkeling experience at age 8 sparked lifelong ocean passion. Witnessed oil spill cleanup volunteers at age 10, shaping conservation mindset.', '8-18 years', 8);

-- CAREER HISTORY
INSERT INTO character_background (character_id, category, period, title, description, date_range, importance_level) VALUES
(1, 'career', '24-26', 'Postdoctoral Researcher', 'Secured competitive postdoc position at Scripps Institution of Oceanography. Launched personal science communication project to bridge academic research and public education. Received early career researcher grant for coral restoration work.', '24-26 years', 9),
(1, 'career', '22-24', 'PhD Research', 'Completed groundbreaking PhD dissertation on coral resilience in warming waters. Published first peer-reviewed paper at 23. Research later featured in National Geographic article.', '22-24 years', 9),
(1, 'career', 'current', 'Marine Research Scientist', 'Active marine biologist conducting cutting-edge research on coral reef ecosystems and marine conservation. Collaborates with local high schools on educational outreach. Combines rigorous scientific research with passionate environmental advocacy.', 'Present', 10);

-- PERSONAL HISTORY
INSERT INTO character_background (character_id, category, period, title, description, date_range, importance_level) VALUES
(1, 'personal', '0-12', 'Coastal Childhood', 'Second-generation Mexican-American who grew up on California coast. Parents immigrated from Baja California, built successful restaurant business. Father was commercial fisherman turned restaurant owner. Strong family traditions around food, ocean connection, and cultural heritage.', '0-12 years', 8),
(1, 'personal', '8-10', 'Ocean Awakening', 'First snorkeling experience at age 8 sparked lifelong passion. Witnessed oil spill cleanup volunteers at age 10, creating deep environmental consciousness. Found bleached coral fragments washed up on beach - early exposure to ocean threats.', '8-10 years', 9),
(1, 'personal', 'formative', 'Grandmother''s Influence', 'Grandmother shared stories about the changing ocean over generations, blending traditional Mexican fishing wisdom with environmental awareness. This intergenerational connection shaped Elena''s approach to marine science - combining cultural heritage with modern conservation.', 'Childhood', 10);

COMMIT;
