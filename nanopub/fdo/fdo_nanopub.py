from nanopub import Nanopub
import json
import rdflib
from typing import Optional
from rdflib.namespace import RDF, RDFS, DCTERMS
from nanopub.namespaces import HDL, FDOF, NPX, FDOC
from nanopub.constants import FDO_PROFILE_HANDLE, FDO_DATA_REF_HANDLE, FDO_DATA_REFS_HANDLE
from nanopub.fdo.fdo_record import FdoRecord
from nanopub.nanopub_conf import NanopubConf
from nanopub.fdo.utils import looks_like_handle, looks_like_url, handle_to_iri


def to_hdl_uri(value):
    if isinstance(value, rdflib.URIRef): 
        return value
    elif isinstance(value, str) and not value.startswith('http'):
        return HDL[value] 
    else:
        raise ValueError(f"Invalid value: {value}")


class FdoNanopub(Nanopub):
    """
    EXPERIMENTAL: This class is experimental and may change or be removed in future versions.
    """
    
    def __init__(self, fdo_id: rdflib.URIRef | str, label: str, fdo_profile: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fdo_uri = to_hdl_uri(fdo_id)  
        self.fdo_profile = fdo_profile
        self._init_core_fdo_triples(label)

    def _init_core_fdo_triples(self, label: str):
        self.assertion.add((self.fdo_uri, RDF.type, FDOF.FAIRDigitalObject))
        self.assertion.add((self.fdo_uri, RDFS.label, rdflib.Literal(label)))
        self.assertion.add((self.fdo_uri, FDOF.hasMetadata, self.metadata.np_uri))
        if self.fdo_profile:
            profile_uri = to_hdl_uri(self.fdo_profile)
            self.assertion.add((self.fdo_uri, DCTERMS.conformsTo, profile_uri))

        self.pubinfo.add((self.metadata.np_uri, RDFS.label, rdflib.Literal(f"FAIR Digital Object: {label}")))
        self.pubinfo.add((self.metadata.np_uri, NPX.introduces, self.fdo_uri))
        
    @classmethod
    def handle_to_nanopub(cls, handle: str, **kwargs) -> "FdoNanopub":
        # To prevent circular import issue
        from nanopub.fdo.retrieve import resolve_handle_metadata
        data = resolve_handle_metadata(handle)
        values = data.get("values", [])

        label = None
        fdo_profile = None
        data_ref = None
        data_refs = []
        other_attributes = []

        for entry in values:
            entry_type = entry.get("type")
            entry_value = entry.get("data", {}).get("value")

            if entry_type == "HS_ADMIN":
                continue
            elif entry_type == "name":
                label = entry_value
            elif entry_type == FDO_PROFILE_HANDLE:
                fdo_profile = entry_value
            elif entry_type == FDO_DATA_REF_HANDLE:
                data_ref = entry_value
            elif entry_type == FDO_DATA_REFS_HANDLE:
                try:
                    data_refs = json.loads(entry_value)
                except json.JSONDecodeError:
                    print("Warning: DataRefs value is not valid JSON:", entry_value)
                    data_refs = []
            else:
                other_attributes.append((entry_type, entry_value))

        np = cls(fdo_id=handle, label=label or handle, fdo_profile=fdo_profile, **kwargs)

        if data_ref:
            np.add_fdo_data_ref(data_ref)
        
        if len(data_refs) > 0:
            for ref in data_refs:
                np.add_fdo_data_ref(ref)

        for attr_type, val in other_attributes:
            np.add_attribute(attr_type, val)

        return np
      
    @classmethod
    def create_with_fdo_iri(cls, 
                    fdo_record: FdoRecord, 
                    fdo_iri: rdflib.URIRef | str, 
                    data_ref: Optional[rdflib.URIRef] = None, 
                    conf: Optional[NanopubConf] = None,
                    ) -> "FdoNanopub":
        if conf is None:
            conf = NanopubConf()
        if isinstance(fdo_iri, str):
            fdo_iri = rdflib.URIRef(fdo_iri) 
        label = fdo_record.get_label() or str(fdo_iri)
        profile = fdo_record.get_profile()

        np = cls(fdo_id=fdo_iri, label=label, fdo_profile=profile, conf=conf)

        if data_ref:
            np.add_fdo_data_ref(data_ref)

        skip_preds = {RDFS.label, DCTERMS.conformsTo, FDOC.hasFdoProfile, FDOF.isMaterializedBy}
        for predicate, obj in fdo_record.tuples.items():
            if predicate in skip_preds:
                continue

            if isinstance(obj, list):
                for o in obj:
                    np.assertion.add((fdo_iri, predicate, o))
            else:
                np.assertion.add((fdo_iri, predicate, obj))

        return np

    @classmethod
    def create_aggregation_fdo(cls,
                    fdo_iri: rdflib.URIRef | str,
                    profile_uri: str,
                    label: str,
                    aggregates: list[str],
                    conf: Optional[NanopubConf] = None,
                    ) -> "FdoNanopub":

        record = FdoRecord(profile_uri=profile_uri, label=label)

        if record.get_data_ref():
            raise ValueError("Aggregate FDOs cannot have a dataRef (isMaterializedBy)")

        for agg in aggregates:
            if looks_like_url(agg):
                iri = rdflib.URIRef(agg)
            elif looks_like_handle(agg):
                iri = handle_to_iri(agg)
            else:
                raise ValueError(f"Invalid aggregate format: {agg}")
            record.add_aggregate(iri)

        npub = cls.create_with_fdo_iri(record, fdo_iri, conf=conf)

        return npub
    
    @classmethod
    def create_derivation_fdo(cls,
                    fdo_iri: rdflib.URIRef | str,
                    profile_uri: str,
                    label: str,
                    sources: list[str],
                    conf: Optional[NanopubConf] = None,
                    ) -> "FdoNanopub":
        """
        Create an FDO nanopub that is derived from one or more source IRIs or handles.
        Adds prov:wasDerivedFrom for each source.
        """
        record = FdoRecord(profile_uri=profile_uri, label=label)

        for source in sources:
            if looks_like_url(source):
                iri = rdflib.URIRef(source)
            elif looks_like_handle(source):
                iri = handle_to_iri(source)
            else:
                raise ValueError(f"Invalid source format: {source}")
            record.add_derivation(iri)

        npub = cls.create_with_fdo_iri(record, fdo_iri, conf=conf)

        return npub


    def add_fdo_profile(self, profile_uri: rdflib.URIRef | str):
        profile_uri = to_hdl_uri(profile_uri)
        self.assertion.add((self.fdo_uri, DCTERMS.conformsTo, profile_uri))
        self.pubinfo.add((HDL[FDO_PROFILE_HANDLE], RDFS.label, rdflib.Literal("FdoProfile")))

    def add_fdo_data_ref(self, data_ref: rdflib.Literal | str):
        target_uri = to_hdl_uri(data_ref)  
        self.assertion.add((self.fdo_uri, FDOF.isMaterializedBy, target_uri))
        self.pubinfo.add((HDL[FDO_DATA_REF_HANDLE], RDFS.label, rdflib.Literal("DataRef")))

    def add_attribute(self, attr_handle: rdflib.URIRef | str, value: rdflib.Literal | str):
        attr_handle = to_hdl_uri(attr_handle) 
        self.assertion.add((self.fdo_uri, attr_handle, rdflib.Literal(value)))

    def add_attribute_label(self, attr_handle: rdflib.URIRef | str, label: str):
        attr_handle = to_hdl_uri(attr_handle) 
        self.pubinfo.add((attr_handle, RDFS.label, rdflib.Literal(label)))
