import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Modal, Platform, Pressable, SafeAreaView, ScrollView,
  Share, StatusBar, StyleSheet, Text, TextInput, View } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import pack from '../data/mobile-pack.json';
import { parseSaved, selectFacilities } from './model.mjs';

const STORAGE = 'accessmap:fictional-gauteng-v1:saved';
const colors = { ink: '#163b43', muted: '#536d71', green: '#116b59', cream: '#f6f7ef',
  line: '#d9e2d9', white: '#ffffff', pale: '#e2eee1', orange: '#f7e2c3' };

function Action({children, onPress, selected = false, disabled = false, label, style}) {
  return <Pressable accessibilityRole="button" accessibilityLabel={label}
    accessibilityState={{selected, disabled}} disabled={disabled} onPress={onPress}
    style={({pressed}) => [styles.action, selected && styles.actionSelected,
      pressed && {opacity: 0.75}, disabled && {opacity: 0.5}, style]}>
    <Text style={[styles.actionText, selected && {color: colors.white}]}>{children}</Text>
  </Pressable>;
}

export default function App() {
  const [tab, setTab] = useState('Explore');
  const [category, setCategory] = useState('all');
  const [query, setQuery] = useState('');
  const [saved, setSaved] = useState([]);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);
  const [saving, setSaving] = useState(false);
  useEffect(() => {
    let active = true;
    AsyncStorage.getItem(STORAGE).then(value => {
      if (active) setSaved(parseSaved(value, pack.facilities));
    }).catch(() => { if (active) setError('Saved places could not be read. You can still explore.'); })
      .finally(() => { if (active) setReady(true); });
    return () => { active = false; };
  }, []);

  async function toggleSave(id) {
    if (!ready || saving) return;
    setSaving(true);
    const next = saved.includes(id) ? saved.filter(x => x !== id) : [...saved, id];
    try {
      await AsyncStorage.setItem(STORAGE, JSON.stringify(next));
      setSaved(next);
      setError('');
    } catch { setError('Could not save on this device. Please try again.'); }
    finally { setSaving(false); }
  }

  async function shareFacility(facility) {
    try {
      await Share.share({message: `AccessMap SA concept: ${facility.name}. FICTIONAL demo facility. ` +
        `${(facility.distance/1000).toFixed(1)} km straight-line from the demo community centre. ` +
        'Not for navigation. Opening hours and services are not verified.'});
    } catch { setError('Sharing is unavailable on this device.'); }
  }

  const rows = selectFacilities(pack, {category, query, savedOnly: tab === 'Saved', saved});
  return <SafeAreaView style={styles.safe}>
    <StatusBar barStyle="dark-content" backgroundColor={colors.cream}/>
    <View style={styles.shell}>
      <View style={styles.header}><Text style={styles.brand}>accessmap<Text style={{color:colors.green}}> sa</Text></Text>
        <View style={styles.badge}><Text style={styles.badgeText}>OFFLINE DEMO</Text></View></View>
      <View style={styles.disclaimer}><Text style={styles.disclaimerText}>Fictional facilities. Explore the concept, not real services.</Text></View>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Text style={styles.eyebrow}>COMMUNITY FIRST</Text>
        <Text style={styles.title}>{tab === 'About' ? 'Small app.\nShared purpose.' : tab === 'Saved' ? 'Your saved\nplaces.' : 'Closer to what\nmatters.'}</Text>
        {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
        {tab === 'About' ? <View style={styles.about}>
          <Text style={styles.sectionTitle}>Built for everyday access</Text>
          <Text style={styles.body}>Browse a small, bundled service directory without an account, GPS permission or a paid map service.</Text>
          <Text style={styles.sectionTitle}>Know what the data can tell you</Text>
          <Text style={styles.body}>Distances use projected straight lines from a fixed demo point. They are not walking routes or travel times. Nearby does not mean open, affordable, safe or available.</Text>
          <Text style={styles.sectionTitle}>Privacy by default</Text>
          <Text style={styles.body}>Bookmarks stay on your device. No analytics, uploads or resident records. Sharing happens only when you choose it.</Text>
          <Text style={styles.sectionTitle}>Before a real community launch</Text>
          <Text style={styles.body}>Replace this fictional pack with licensed and locally verified data. Test with residents, including people using assistive technology. The government edition remains a research question.</Text>
        </View> : <>
          <View style={styles.location}><Text style={styles.locationLabel}>EXPLORING FROM</Text><Text style={styles.locationName}>Demo community centre</Text><Text style={styles.body}>Fixed sample point · Gauteng</Text></View>
          <TextInput accessibilityLabel="Search facilities" placeholder="Search a clinic or library" placeholderTextColor={colors.muted}
            value={query} onChangeText={setQuery} style={styles.search} autoCorrect={false}/>
          <View style={styles.filters}>{[['all','All places'],['clinic','Clinics'],['library','Libraries']].map(([id,name]) =>
            <Action key={id} selected={category === id} onPress={() => setCategory(id)}>{name}</Action>)}</View>
          <View style={styles.resultHeader}><Text style={styles.sectionTitle}>{tab === 'Saved' ? 'Saved on this device' : 'Places to explore'}</Text><Text style={styles.body}>{rows.length} places</Text></View>
          <Text style={styles.caption}>Nearest first · straight-line distance</Text>
          {!ready ? <ActivityIndicator accessibilityLabel="Loading saved places" color={colors.green}/> : null}
          {rows.map(f => <Pressable key={f.id} accessibilityRole="button" accessibilityLabel={`View ${f.name}`}
            onPress={() => setSelected(f)} style={({pressed}) => [styles.facility, pressed && {opacity:0.75}]}>
            <View style={[styles.facilityIcon, f.category === 'library' && {backgroundColor:'#eee4f1'}]}><Text style={styles.symbol}>{f.category === 'clinic' ? '+' : 'L'}</Text></View>
            <View style={styles.facilityInfo}><Text style={styles.category}>{f.category.toUpperCase()} · DEMO</Text><Text style={styles.facilityName}>{f.name}</Text><Text style={styles.body}>Hours not verified</Text></View>
            <View style={styles.distance}><Text style={styles.distanceValue}>{(f.distance/1000).toFixed(1)}</Text><Text style={styles.body}>km</Text>{saved.includes(f.id) ? <Text style={styles.savedTag}>Saved</Text> : null}</View>
          </Pressable>)}
          {!rows.length ? <View style={styles.about}><Text style={styles.sectionTitle}>{tab === 'Saved' ? 'No saved places match.' : 'No matching places.'}</Text><Text style={styles.body}>Try another search or category. Missing records do not mean services do not exist.</Text><Action onPress={() => {setQuery('');setCategory('all');}}>Clear filters</Action></View> : null}
          <View style={styles.note}><Text style={styles.sectionTitle}>Good information starts locally.</Text><Text style={styles.body}>This concept shares a tiny data pack with the QGIS project. Real places need community verification.</Text></View>
        </>}
      </ScrollView>
      <View style={styles.nav}>{['Explore','Saved','About'].map(name => <Action key={name} selected={tab === name} onPress={() => setTab(name)} style={{flex:1}}>{name}</Action>)}</View>
    </View>
    <Modal visible={!!selected} transparent animationType="slide" onRequestClose={() => setSelected(null)}>
      <View style={styles.scrim}><SafeAreaView style={styles.sheet}><ScrollView contentContainerStyle={styles.sheetContent}>
        {selected && <><Action onPress={() => setSelected(null)}>Close details</Action><Text style={styles.eyebrow}>{selected.category.toUpperCase()} / FICTIONAL</Text>
          <Text style={styles.title}>{selected.name}</Text><Text style={styles.sectionTitle}>{(selected.distance/1000).toFixed(1)} km straight-line</Text>
          <Text style={styles.body}>From the fixed demo community centre. Not a walking route.</Text>
          <View style={styles.location}><Text style={styles.sectionTitle}>Verification required</Text><Text style={styles.body}>Opening hours, accessibility, contact details and services have not been verified. This facility is fictional.</Text></View>
          <Action selected={saved.includes(selected.id)} disabled={!ready || saving} onPress={() => toggleSave(selected.id)}>{saving ? 'Saving…' : saved.includes(selected.id) ? 'Remove from saved places' : 'Save on this device'}</Action>
          <Action onPress={() => shareFacility(selected)}>Share demo details</Action>
          {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
        </>}
      </ScrollView></SafeAreaView></View>
    </Modal>
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  safe:{flex:1,backgroundColor:colors.cream,paddingTop:Platform.OS==='android'?StatusBar.currentHeight:0},
  shell:{flex:1,width:'100%',maxWidth:620,alignSelf:'center'},header:{padding:20,flexDirection:'row',alignItems:'center',justifyContent:'space-between',gap:10},
  brand:{fontSize:24,fontWeight:'800',color:colors.ink,letterSpacing:-1},badge:{backgroundColor:colors.pale,padding:8,borderRadius:20},badgeText:{color:colors.green,fontSize:10,fontWeight:'800'},
  disclaimer:{backgroundColor:colors.orange,paddingHorizontal:20,paddingVertical:10},disclaimerText:{fontSize:12,color:'#67410c',lineHeight:18},
  content:{padding:22,paddingBottom:30,gap:16},eyebrow:{fontSize:11,color:colors.green,fontWeight:'800',letterSpacing:2,marginTop:10},
  title:{fontSize:42,lineHeight:46,fontWeight:'800',color:colors.ink,letterSpacing:-1.6},body:{fontSize:14,lineHeight:21,color:colors.muted},
  location:{padding:18,backgroundColor:colors.pale,borderRadius:18,gap:5},locationLabel:{fontSize:10,letterSpacing:1,color:colors.green,fontWeight:'700'},locationName:{fontSize:18,fontWeight:'700',color:colors.ink},
  search:{minHeight:52,borderRadius:14,backgroundColor:colors.white,borderWidth:1,borderColor:colors.line,paddingHorizontal:16,fontSize:16,color:colors.ink},
  filters:{flexDirection:'row',flexWrap:'wrap',gap:8},action:{minHeight:46,paddingHorizontal:16,paddingVertical:12,borderRadius:14,backgroundColor:colors.white,alignItems:'center',justifyContent:'center',borderWidth:1,borderColor:colors.line},
  actionSelected:{backgroundColor:colors.green,borderColor:colors.green},actionText:{fontSize:14,fontWeight:'600',color:colors.ink},
  resultHeader:{flexDirection:'row',justifyContent:'space-between',alignItems:'center',gap:10,flexWrap:'wrap'},sectionTitle:{fontSize:17,fontWeight:'700',color:colors.ink,lineHeight:24},caption:{fontSize:12,color:colors.muted,marginTop:-10},
  facility:{flexDirection:'row',gap:12,alignItems:'center',backgroundColor:colors.white,padding:16,borderRadius:18,borderWidth:1,borderColor:colors.line},
  facilityIcon:{width:42,height:46,borderRadius:13,backgroundColor:colors.pale,justifyContent:'center',alignItems:'center'},symbol:{fontSize:26,fontWeight:'700',color:colors.ink},facilityInfo:{flex:1,gap:4},
  category:{fontSize:9,fontWeight:'700',letterSpacing:1,color:colors.green},facilityName:{fontSize:16,lineHeight:22,fontWeight:'700',color:colors.ink},distance:{alignItems:'flex-end'},distanceValue:{fontSize:22,fontWeight:'700',color:colors.ink},savedTag:{fontSize:11,color:colors.green},
  note:{padding:20,borderRadius:18,backgroundColor:colors.pale,gap:8,marginTop:8},about:{gap:16},nav:{flexDirection:'row',gap:8,padding:12,borderTopWidth:1,borderColor:colors.line,backgroundColor:colors.cream},
  error:{color:'#a02c29',fontSize:14,lineHeight:21},scrim:{flex:1,backgroundColor:'#00000066',justifyContent:'flex-end'},sheet:{maxHeight:'90%',backgroundColor:colors.cream,borderTopLeftRadius:24,borderTopRightRadius:24},sheetContent:{padding:24,gap:20}
});
