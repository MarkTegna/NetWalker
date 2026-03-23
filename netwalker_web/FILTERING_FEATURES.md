# NetWalker Web UI - Advanced Filtering Features

## Overview

Enhanced the NetWalker Web UI with comprehensive filtering capabilities and Excel export functionality following the `YYYYMMDD-HH-MM` naming standard.

## New Features

### 1. Advanced Device Filtering

**Location**: `/devices.html`

**Filter Fields**:
- Device Name (partial match)
- Platform (partial match)
- Hardware Model (partial match)
- IP Address (partial match)
- Serial Number (partial match)
- Software Version (partial match)
- Capabilities (partial match)

**Features**:
- ✅ Real-time record count display
- ✅ Filtered indicator badge
- ✅ Collapsible filter panel
- ✅ Clear all filters button
- ✅ Pagination (50 records per page)
- ✅ Load more functionality
- ✅ Responsive Bootstrap UI

### 2. Excel Export with Filters

**Export Button**: Available on every results page

**Features**:
- ✅ Exports filtered results (respects current filters)
- ✅ Filename format: `Device_Inventory_YYYYMMDD-HH-MM.xlsx`
- ✅ Example: `Device_Inventory_20260224-18-30.xlsx`
- ✅ Professional Excel formatting
- ✅ Auto-sized columns
- ✅ Header styling

**Export Endpoints**:
- `GET /api/reports/devices` - Device inventory (with filters)
- `GET /api/reports/stacks` - Stack members

### 3. Enhanced API Endpoints

**Updated Endpoints**:

```
GET /api/devices
  Query Parameters:
    - limit (1-1000, default: 50)
    - offset (default: 0)
    - device_name (optional)
    - platform (optional)
    - hardware_model (optional)
    - serial_number (optional)
    - capabilities (optional)
    - ip_address (optional)
    - software_version (optional)

GET /api/devices/count
  Query Parameters:
    - Same filters as above
  Returns:
    - count: Total matching records
    - filtered: Boolean indicating if filters applied

GET /api/reports/devices
  Query Parameters:
    - Same filters as /api/devices
  Returns:
    - Excel file download
```

## Usage Examples

### Example 1: Filter by Platform

**UI**:
1. Go to `/devices.html`
2. Enter "Cisco IOS-XE" in Platform field
3. Click "Apply Filters"
4. Click "Export to Excel"

**API**:
```
GET /api/devices?platform=Cisco%20IOS-XE&limit=50
GET /api/reports/devices?platform=Cisco%20IOS-XE
```

### Example 2: Filter by IP Subnet

**UI**:
1. Enter "10.1" in IP Address field
2. Click "Apply Filters"

**API**:
```
GET /api/devices?ip_address=10.1
```

### Example 3: Multiple Filters

**UI**:
1. Enter "CORE" in Device Name
2. Enter "C9300" in Hardware Model
3. Click "Apply Filters"

**API**:
```
GET /api/devices?device_name=CORE&hardware_model=C9300
```

### Example 4: Export Filtered Results

**UI**:
1. Apply any filters
2. Click "Export to Excel" button
3. File downloads as: `Device_Inventory_20260224-18-30.xlsx`

**API**:
```
GET /api/reports/devices?device_name=CORE&hardware_model=C9300
```

## File Changes

### Backend Changes

**Modified Files**:
1. `backend/database.py`
   - Updated `get_all_devices()` to accept filters parameter
   - Updated `get_device_count()` to accept filters parameter
   - Added dynamic WHERE clause building

2. `backend/api/devices.py`
   - Added filter query parameters to `/devices` endpoint
   - Added filter query parameters to `/devices/count` endpoint
   - Returns filtered indicator in count response

3. `backend/api/reports.py`
   - Added filter query parameters to `/reports/devices` endpoint
   - Updated filename format to `YYYYMMDD-HH-MM`
   - Updated `/reports/stacks` filename format

### Frontend Changes

**New Files**:
1. `frontend/devices.html`
   - Complete device inventory page
   - Advanced filter panel
   - Results table with pagination
   - Export button
   - Record count display

2. `frontend/static/js/devices.js`
   - Filter form handling
   - Dynamic device loading
   - Pagination logic
   - Export functionality
   - Count updates

**Modified Files**:
1. `frontend/index.html`
   - Added navigation link to Device Inventory
   - Added Quick Actions section

## Database Query Performance

### Optimizations

**Indexed Columns Used**:
- `devices.status` (indexed)
- `devices.device_name` (part of unique constraint)
- `device_interfaces.ip_address` (indexed)
- `device_versions.last_seen` (indexed)

**Query Strategy**:
- Uses `LIKE` with wildcards for partial matching
- Uses `EXISTS` subqueries for related tables (interfaces, versions)
- Pagination with `OFFSET/FETCH` for large result sets
- Filters applied at database level (not in application)

### Performance Tips

1. **Use specific filters** - More specific = faster queries
2. **Avoid leading wildcards** - `%CORE` slower than `CORE%`
3. **Limit results** - Use pagination for large datasets
4. **Index usage** - Filters on indexed columns are fastest

## Testing

### Test the Features

1. **Start the application**:
   ```powershell
   cd netwalker_web
   .\start.ps1
   ```

2. **Access Device Inventory**:
   - Open: http://localhost:8000/devices.html

3. **Test Filtering**:
   - Enter partial device name
   - Click "Apply Filters"
   - Verify record count updates
   - Verify filtered indicator appears

4. **Test Export**:
   - Apply filters (or leave empty for all)
   - Click "Export to Excel"
   - Verify filename format: `Device_Inventory_YYYYMMDD-HH-MM.xlsx`
   - Open Excel file and verify data

5. **Test API**:
   - Open: http://localhost:8000/docs
   - Try `/api/devices` with filter parameters
   - Try `/api/devices/count` with filters
   - Try `/api/reports/devices` with filters

## Future Enhancements

### Potential Additions

1. **Saved Filters**
   - Save favorite filter combinations
   - Quick filter presets

2. **Advanced Operators**
   - Exact match vs. partial match toggle
   - NOT filters (exclude)
   - OR conditions

3. **Date Range Filters**
   - Filter by first_seen date
   - Filter by last_seen date

4. **Bulk Operations**
   - Select multiple devices
   - Bulk export
   - Bulk actions

5. **Column Selection**
   - Choose which columns to display
   - Choose which columns to export

6. **Sort Options**
   - Sort by any column
   - Multi-column sorting

7. **Export Formats**
   - CSV export
   - JSON export
   - PDF reports

## Troubleshooting

### Issue: Filters not working

**Solution**:
- Check browser console for errors
- Verify API endpoint returns data
- Check database connection

### Issue: Export downloads empty file

**Solution**:
- Verify filters return results
- Check `reports/` directory permissions
- Check browser download settings

### Issue: Slow query performance

**Solution**:
- Use more specific filters
- Reduce page size
- Check database indexes
- Review query execution plan

## API Documentation

Full interactive API documentation available at:
- http://localhost:8000/docs

## Support

For issues or questions:
- Review `DATABASE_SCHEMA.md` for database structure
- Check API documentation at `/docs`
- Review browser console for errors
- Check application logs

## Version

Feature Version: 0.1.0  
Date Added: 2026-02-24  
Author: Mark Oldham
