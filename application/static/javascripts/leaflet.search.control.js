L.control.search = (function(L) {
  L.Control.Search = L.Control.extend({
    options: {
      textPlaceholder: "enter UK address",
      position: 'topleft'
    },
    initialize: function(options) {
      L.Util.setOptions(this, options || {});
    },
    onAdd: function(map) {
      this._map = map;
      this._container = L.DomUtil.create('div', 'leaflet-control-search');
      this._form = this._createForm('leaflet-form');
      this._input = this._createInput(this.options.textPlaceholder, 'search-input');
      this._button = this._createButton('Search', 'search-button');
      return this._container;
    },
    onRemove: function(map) {
      console.log("removing search control");
    },
    _createForm: function(className) {
      var form = L.DomUtil.create('form', className, this._container);
      L.DomEvent
        .on(form, 'submit', L.DomEvent.stop, this)
        .on(form, 'submit', this._handleSubmit, this);
      return form;
    },
    _createInput: function (text, className) {
    		var label = L.DomUtil.create('label', className, this._form);
    		var input = L.DomUtil.create('input', className, this._form);
    		input.type = 'text';
    		input.value = '';
    		input.autocomplete = 'off';
    		input.autocorrect = 'off';
    		input.autocapitalize = 'off';
    		input.placeholder = text;
    		input.role = 'search';
    		input.id = 'leaflet-search-box';

    		label.htmlFor = input.id;
    		label.style.display = 'none';
    		label.value = text;

    		return input;
    	},
      _createButton: function (title, className) {
    		var button = L.DomUtil.create('a', className, this._container);
    		button.href = '#';
    		button.title = title;

    		L.DomEvent
    			.on(button, 'click', L.DomEvent.stop, this)
          .on(button, 'click', this._handleSubmit, this);

    		return button;
    	},
      _handleSubmit: function(e) {
        var term = this._input.value;
        this._performSearch(term);
      },
      _performSearch: function(query) {
        var _map = this._map;
        geoUtils.performGeocode(query, function(data) {
          if( data.success ) {
            _map.panTo(new L.LatLng(data.lat, data.lng));
          } else {
            console.log("Geo search unsuccessful");
          }
        });
      }
  });
  return function (options) {
      return new L.Control.Search(options);
  };
}).call(this, L);
