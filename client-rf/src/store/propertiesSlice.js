import {createSlice} from '@reduxjs/toolkit';

const initialState = {
  properties: [],
};

export const propertiesSlice = createSlice({
  name: 'properties',
  initialState,
  reducers: {
    addSavedProperty: (state, action) => {
      const newProperty = action.payload.property;
      const existingProperty = state.properties.find(
        item => item.id === newProperty.id,
      );
      if (existingProperty) {
        state.properties = state.properties.filter(item => item.id !== existingProperty.id) // Remove item with specified ID
        return
        // Property already exists as a saved property
      } else {
        // state.properties.push({property: newProperty});
        state.properties.push(newProperty);
      }
    },
    removeSavedProperty: (state, action) => {
        const property = action.payload.property;
        const existingProperty = state.properties.find(
            item => item.id === property.id,
        );
        if (existingProperty) {
            state.properties = state.properties.filter(item => item.id !== property.id) // Remove item with specified ID
            return
            // Property already exists as a saved property
        } else {
            state.properties.push({property: property});
        }
    },
    clearSavedProperties: (state) => {
      state.properties = [];
    }
  },
});

export const numberOfSavedProperties = state => state.cart.properties.length;
