/**
 * @jest-environment jsdom
*/

import { TextEncoder, TextDecoder } from 'util';
Object.assign(global, { TextEncoder, TextDecoder });

// Mock global browser APIs
global.fetch   = jest.fn();
global.alert   = jest.fn();
global.confirm = jest.fn();
 
let saveTemplateChanges,
    delete_template,
    revertTemplateChanges,
    confirmDeleteField,
    addNewField,
    deleteField;

beforeEach(() => {
  // 1) Reset the module registry so require() loads a fresh copy
  jest.resetModules();

  // 2) Stub out the DOM exactly as your module expects
  document.body.innerHTML = `
    <div id="template-data"
         data-session-mode="edit"
         data-templates='{"name":"test","columns":["A","C"]}'
         data-fields='[{"name":"field1"}]'>
    </div>

    <input id="template-name" value="test"/>

    <input type="checkbox" name="columns" value="A" checked/>
    <input type="checkbox" name="columns" value="B"/>
    <input type="checkbox" name="columns" value="C" checked/>

    <div id="loading" style="display:none"></div>
    <button id="save-fields-btn"    style="display:none"></button>
    <button id="revert-fields-btn"  style="display:none"></button>
    <select id="new-field-select"></select>
    <div    id="field-popup"        style="display:none"></div>
  `;

  // 3) Stub out the globals your module reads
  global.session_mode          = '';
  global.currentTemplate       = 'test';
  global.templatesDict         = { test: ['A','B'] };
  global.originalTemplatesDict = { test: ['A','B'] };
  global.all_fields            = ['A','B','C','D'];
  global.hasChanges            = false;
  global.loading               = document.getElementById('loading');

  // 4) Now load your module under test
  const templates = require('../../static/js/templates.js');
  saveTemplateChanges   = templates.saveTemplateChanges;
  delete_template       = templates.delete_template;
  revertTemplateChanges = templates.revertTemplateChanges;
  confirmDeleteField    = templates.confirmDeleteField;
  addNewField           = templates.addNewField;
  deleteField           = templates.deleteField;
});

describe('saveTemplateChanges', () => {
  beforeEach(() => {
    // Simulate user-selected fields in the DOM
    document.body.innerHTML += `
      <div class="templates-field-name">A</div>
      <div class="templates-field-name">C</div>
    `;
  });

  test('user made changes triggers fetch and updates UI', async () => {
    fetch.mockResolvedValue({
      json: () => Promise.resolve({ message: true })
    });

    const saveBtn = document.getElementById('save-fields-btn');
    const revBtn  = document.getElementById('revert-fields-btn');

    expect(global.hasChanges).toBe(false);

    await saveTemplateChanges();

    // loading shown then hidden
    expect(global.loading.style.display).toBe('none');

    // correct payload
    expect(fetch).toHaveBeenCalledWith(
      '/api/update_template',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'test', columns: ['A','C'] })
      }
    );

    expect(alert).toHaveBeenCalledWith('Template updated successfully!');
    expect(global.hasChanges).toBe(false);
    expect(saveBtn.style.display).toBe('none');
    expect(revBtn.style.display).toBe('none');
    expect(global.originalTemplatesDict.test).toEqual(['A','C']);
  });

  test('no changes still calls fetch with original columns', async () => {
    // override querySelectorAll to return original A,B
    document.querySelectorAll = () => [
      { textContent: 'A' }, { textContent: 'B' }
    ];
    fetch.mockResolvedValue({ json: () => Promise.resolve({ message: true }) });

    await saveTemplateChanges();

    expect(fetch).toHaveBeenCalledWith(
      '/api/update_template',
      expect.objectContaining({
        body: JSON.stringify({ name: 'test', columns: ['A','B'] })
      })
    );
  });

  test('view mode does nothing', async () => {
    global.session_mode = 'view';
    fetch.mockClear();

    await saveTemplateChanges();
    expect(fetch).not.toHaveBeenCalled();
  });
});

describe('delete_template', () => {
  test('confirmed deletion triggers fetch and removes row', async () => {
    // create a DOM row to be removed
    const row = document.createElement('div');
    row.id = 'template-testName';
    document.body.appendChild(row);

    confirm.mockReturnValue(true);
    fetch.mockResolvedValue({ json: () => Promise.resolve({ message: true }) });

    await delete_template('testName');

    expect(confirm).toHaveBeenCalledWith(
      'Are you sure you want to delete the template "testName"?'
    );
    expect(fetch).toHaveBeenCalledWith(
      '/api/delete_template',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ name: 'testName' })
      })
    );
    expect(document.getElementById('template-testName')).toBeNull();
  });

  test('canceled deletion does nothing', async () => {
    confirm.mockReturnValue(false);
    fetch.mockClear();

    await delete_template('testName');
    expect(fetch).not.toHaveBeenCalled();
  });
});

describe('revertTemplateChanges', () => {
  beforeEach(() => {
    global.loadTemplateFields = jest.fn();
    global.originalTemplatesDict.test = ['X','Y'];
    global.templatesDict.test         = ['A','B'];
    global.hasChanges                 = true;
  });

  test('confirm & changes present', () => {
    confirm.mockReturnValue(true);
    revertTemplateChanges();
    expect(global.templatesDict.test).toEqual(['X','Y']);
    expect(global.loadTemplateFields).toHaveBeenCalledWith('test', false);
    expect(global.hasChanges).toBe(false);
  });

  test('confirm & no changes skips reload', () => {
    global.hasChanges = false;
    confirm.mockReturnValue(true);
    revertTemplateChanges();
    expect(global.loadTemplateFields).not.toHaveBeenCalled();
  });

  test('cancel leaves everything', () => {
    confirm.mockReturnValue(false);
    revertTemplateChanges();
    expect(global.templatesDict.test).toEqual(['A','B']);
  });
});

describe('confirmDeleteField', () => {
  beforeEach(() => {
    global.deleteField = jest.fn();
  });

  test('confirm calls deleteField', () => {
    confirm.mockReturnValue(true);
    confirmDeleteField('Field1');
    expect(global.deleteField).toHaveBeenCalledWith('Field1');
  });

  test('cancel does nothing', () => {
    confirm.mockReturnValue(false);
    confirmDeleteField('Field1');
    expect(global.deleteField).not.toHaveBeenCalled();
  });
});

describe('addNewField', () => {
  beforeEach(() => {
    global.loadTemplateFields = jest.fn();
    document.getElementById('new-field-select').innerHTML =
      `<option value="">-- Select --</option>`;
  });

  test('adding a new field works', () => {
    const select = document.getElementById('new-field-select');
    select.innerHTML += `<option value="C">C</option>`;
    select.value = 'C';

    addNewField();

    expect(global.templatesDict.test).toContain('C');
    expect(global.loadTemplateFields).toHaveBeenCalledWith('test', true);
    expect(global.hasChanges).toBe(true);
    expect(document.getElementById('save-fields-btn').style.display)
      .toBe('inline-block');
    expect(document.getElementById('revert-fields-btn').style.display)
      .toBe('inline-block');
    expect(document.getElementById('field-popup').style.display)
      .toBe('none');
  });

  test('no selection alerts', () => {
    document.getElementById('new-field-select').value = '';
    addNewField();
    expect(alert).toHaveBeenCalledWith('Please select a field.');
    expect(document.getElementById('field-popup').style.display)
      .toBe('none');
  });

  test('selecting existing field alerts', () => {
    const select = document.getElementById('new-field-select');
    select.innerHTML += `<option value="A">A</option>`;
    select.value = 'A';

    addNewField();
    expect(alert).toHaveBeenCalledWith('Field already exists in the template.');
    expect(document.getElementById('field-popup').style.display)
      .toBe('none');
  });
});
