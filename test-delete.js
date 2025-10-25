const fs = require('fs');
const path = require('path');

function readPrompts() {
  try {
    const filePath = path.join(__dirname, 'data', 'system-prompts.json');
    console.log('Reading from:', filePath);
    if (!fs.existsSync(filePath)) {
      console.log('File does not exist');
      return [];
    }
    const data = fs.readFileSync(filePath, 'utf8');
    console.log('Raw data length:', data.length, 'chars');
    const parsed = JSON.parse(data);
    console.log('Parsed:', parsed.length, 'prompts');
    return parsed;
  } catch (error) {
    console.error('Error:', error);
    return [];
  }
}

function deletePrompt(id) {
  console.log('Deleting prompt with id:', id);
  const prompts = readPrompts();
  console.log('Read', prompts.length, 'prompts');
  console.log('Prompts before filter:', prompts.map(p => p.id));
  const filteredPrompts = prompts.filter(p => p.id !== id);
  console.log('After filtering:', filteredPrompts.length, 'prompts');
  console.log('Filtered result:', filteredPrompts.map(p => p.id));

  if (filteredPrompts.length === prompts.length) {
    console.log('No prompt found with id:', id);
    return false;
  }

  // Actually write
  const filePath = path.join(__dirname, 'data', 'system-prompts.json');
  fs.writeFileSync(filePath, JSON.stringify(filteredPrompts, null, 2));
  console.log('Successfully wrote to file');
  return true;
}

console.log('Testing delete function...');
deletePrompt('176123658325774hny5skd');
