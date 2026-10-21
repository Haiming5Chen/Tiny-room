"""Export candidate actuators and custom geometry without implying build readiness."""
import csv
import io
from little_world.core.component import Body,Motor


def build_report(blueprint):
    out=io.StringIO();writer=csv.writer(out)
    writer.writerow(('component','type','candidate_model','quantity','evidence','voltage_V','operating_cap_Nm','stall_Nm','no_load_rpm','source','source_checked','parent','shape','size_m','material','limitations'))
    for c in blueprint.components:
        if isinstance(c,Motor):
            p=c.profile
            writer.writerow((c.id,'actuator',p.model if p else 'Unassigned',1,
                'Manufacturer endpoints; estimated envelope; not measured' if p else 'Ideal approximation',
                p.voltage if p else '',c.max_torque,p.stall_torque if p else '',p.no_load_rpm if p else '',
                p.source if p else '',p.checked_on if p else '',c.joint,'','','',
                'Candidate only: mounting and mass not modeled; operating cap is an assumption; continuous capability unknown; no current/thermal/firmware model'))
        elif isinstance(c,Body) and c.robot_asset and c.robot_asset.startswith('user:'):
            from little_world.assets.robot_models import asset_root,title
            import json
            source=json.loads((asset_root(c.robot_asset)/'SOURCE.json').read_text())
            writer.writerow((c.id,'imported robot',title(c.robot_asset),1,
                'Imported from its own '+source['format']+' file; servos added by the importer where it had none (ADR 0044); not physical validation',
                '','','','',source['file'],source['imported'],
                c.parent or '','mesh assembly','fixed','file materials',
                'Geometry, inertias and limits as its file gives them; not a purchase specification or calibrated digital twin'))
        elif isinstance(c,Body) and c.robot_asset:
            from little_world.assets.robot_models import asset_root,MODELS
            import json
            source=json.loads((asset_root(c.robot_asset)/'SOURCE.json').read_text())
            writer.writerow((c.id,'registered robot',MODELS[c.robot_asset][2],1,
                'MuJoCo Menagerie model; not physical validation','','','','',source['repository'],source['revision'],
                c.parent or '','mesh assembly','fixed','upstream materials',
                'Original geometry, inertias, limits and servos; not a purchase specification or calibrated digital twin'))
        elif isinstance(c,Body):
            writer.writerow((c.id,'custom geometry','Custom / no vendor part',1,'Approximate',
                '','','','','','',c.parent or '',c.geometry.shape,' '.join(map(str,c.geometry.size)),c.material,
                'Not a purchase item or fabrication drawing; hardware, wiring and fit unresolved'))
    return out.getvalue()
