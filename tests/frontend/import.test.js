/**
 * @jest-environment jsdom
 */

// Mock DOM elements required by submitMappingData
document.body.innerHTML = `
  <table id="map-data">
    <tbody>
      <tr><td><select><option value="last_name" selected></option></select></td></tr>
    </tbody>
  </table>
  <div id="preview-table-body"></div>
  <div id="new-students-table-container" style="display: block;"></div>
`;

// Mock window properties and functions
window.selectedExcelFields = ['Last Name'];
window.mappingRules = [
  {
    excel: ['ID'],
    susandb: ['student_id']
  }
];

jest.spyOn(window, 'alert').mockImplementation(() => {});
delete window.location;
window.location = { href: '' }; // Mock location

//Must spy before importing the function
import {displayPreviewTable, displayNewStudentsTable} from '../../static/js/fields_to_update.js';
const mocked = {
    displayPreviewTable,
    displayNewStudentsTable
}
jest.spyOn(mocked, 'displayPreviewTable').mockReturnValue('');
jest.spyOn(mocked, 'displayNewStudentsTable').mockReturnValue('')

import {submitMappingData} from '../../static/js/fields_to_update.js';

describe('submitMappingData', () => {
    it("should run", () => {
        mocked.displayPreviewTable();
        expect(mocked.displayPreviewTable).toHaveBeenCalled();
    });
});

describe('submitMappingData', () => {
    beforeEach(() => {
        //jest.clearAllMocks();
        //window.location.href = '';
        });

  it('handles all student IDs found in the database (only updates)', async () => {
    // Mock fetch response
    const mockResponse = {
      preview: [
        {
          student_id: "101",
          first_name: "Jane",
          last_name: "Doe",
          changes: [
            {
              field: "last_name",
              current_value: "Doe",
              new_value: "Smith",
              unchanged: false
            }
          ]
        }
      ],
      new_students: [],
      change_applied: true
    };

    global.fetch = jest.fn().mockResolvedValue({
      json: () => Promise.resolve(mockResponse)
    });
const fakePreviewTable = jest.fn(()=>"");

    submitMappingData(fakePreviewTable);

    expect(fakePreviewTable).toHaveBeenCalledWith(mockResponse.preview);
    expect(mocked.displayNewStudentsTable).not.toHaveBeenCalled();
    expect(window.location.href).toBe('');
    expect(window.alert).not.toHaveBeenCalled();
  });
});
/*
  it('handles some student IDs not found in the database (new students present)', async () => {
    // Mock fetch response
    const mockResponse = {
      preview: [],
      new_students: [
        {
          student_id: "999",
          first_name: "Alice",
          last_name: "Wonder",
          raw_values: {
            email: "alice@example.com"
          }
        }
      ],
      change_applied: false
    };

    global.fetch = jest.fn().mockResolvedValue({
      json: () => Promise.resolve(mockResponse)
    });

    fetch.submitMappingData();

    expect(fetch.displayPreviewTable).not.toHaveBeenCalled();
    expect(fetch.displayNewStudentsTable).toHaveBeenCalledWith(mockResponse.new_students);
    expect(window.alert).not.toHaveBeenCalled();
    expect(window.location.href).toBe('');
  });
});*/