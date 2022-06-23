#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 20 14:58:31 2022

@author: benoit
"""

from neuron import h#, gui
from neuron.units import ms, mV
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.animation import ArtistAnimation
# from xcell import visualizers
import xcell

import Common
import time
import pickle


from xcell import nrnutil as nUtil
from matplotlib.lines import Line2D

h.load_file('stdrun.hoc')
h.CVode().use_fast_imem(1)


nRing=5
nSegs=1

ring=Common.Ring(N=1,stim_delay=0)
# shape_window=h.PlotShape(True)
# shape_window.show(0)


for cell in ring.cells:
    cell.dend.nseg=nSegs
    h.define_shape()

#





ivecs, isSphere, coords, rads = nUtil.getNeuronGeometry()

t = h.Vector().record(h._ref_t)
h.finitialize(-65 * mV)
h.continuerun(20)



I=-1e-9*np.array(ivecs).transpose()
imax=np.max(np.abs(I))
cmap,norm=xcell.visualizers.getCmap(I.ravel(),forceBipolar=True,logscale=True)

# fig=plt.figure()
# ax=plt.gca()

coord=np.array(coords)
xmax=1.5*np.max(np.concatenate(
    (np.max(coord,axis=0), np.min(coord,axis=0))
    ))


x,y,z=np.hsplit(coord,3)

tht=np.linspace(0,2*np.pi)

#to numpy arrays
selSphere=np.array(isSphere)
rvec=np.array(rads)



lastNumEl=0
lastI=0


tv=np.array(t)*1e-3



study,setup = Common.makeSynthStudy('NEURON/ring'+str(nRing),xmax=xmax)
setup.currentSources=[]
studyPath=study.studyPath

strat='depth'
dmax=9
dmin=6

vids=True
nskip=4
# nskip=len(tv)

# tdata={
#        'x': tv}

if vids:
    img=xcell.visualizers.SingleSlice(None,study,
                                      tv)
    nUtil.showCellGeo(img.axes[0])


    # err=xcell.visualizers.SingleSlice(None, study,
    #                                   tv)


for r,c,v in zip(rads,coords, I[0]):
    setup.addCurrentSource(v, c,r)

tmax=tv.shape[0]
errdicts=[]

for ii in range(0,tmax,nskip):

    t0=time.monotonic()
    ivals=I[ii]
    tval=tv[ii]

    setup.currentTime=tval

    changed=False
    # metrics=[]

    iscale=1-np.abs(ivals)/imax
    for jj in range(len(setup.currentSources)):
        ival=ivals[jj]
        setup.currentSources[jj].value=ival



    if strat=='k':
        ################ k-param strategy
        density=0.4*np.max(iscale)
        # print('density:%.2g'%density)

    elif strat=='depth' or strat=='d2':
        ##################### Depth strategy
        scale=(dmax-dmin)*np.max(iscale)
        dint,dfrac=divmod(scale, 1)
        maxdepth=dmin+int(dint)
        # print('depth:%d'%maxdepth)


        # density=0.25
        if strat=='d2':
            density=0.5
        else:
            density=0.2#+0.2*dfrac

    elif strat=='fixed':
        ################### Static mesh
        maxdepth=5
        density=0.2


        # metrics.append(xcell.makeExplicitLinearMetric(maxdepth, density))

    metrics=xcell.makeScaledMetrics(coords, iscale, maxdepth)
    changed=setup.makeAdaptiveGrid(metrics, maxdepth)




    if changed:
        setup.meshnum+=1
        setup.finalizeMesh()

        numEl=len(setup.mesh.elements)


        setup.setBoundaryNodes()

        v=setup.iterativeSolve()
        lastNumEl=numEl
        setup.iteration+=1

        study.saveData(setup)#,baseName=str(setup.iteration))
    else:
        vdof=setup.getDoFs()
        # v=setup.iterativeSolve(vGuess=vdof)
        #TODO: vguess slows things down?

        v=setup.iterativeSolve()


    dt=time.monotonic()-t0

    lastI=ival

    study.newLogEntry(['Timestep','Meshnum'],[setup.currentTime, setup.meshnum])

    setup.stepLogs=[]

    print('%d percent done'%(int(100*ii/tmax)))






    errdict=xcell.misc.getErrorEstimates(setup)
    errdict['densities']=density
    errdict['depths']=maxdepth
    errdict['numels']=lastNumEl
    errdict['dt']=dt
    errdict['vMax']=max(np.abs(v))
    errdicts.append(errdict)


    if vids:
        # err.addSimulationData(setup,append=True)
        img.addSimulationData(setup,append=True)

lists=xcell.misc.transposeDicts(errdicts)
pickle.dump(lists, open(studyPath+strat+'.p','wb'))
    # scat=ax.scatter(x,y,c=I[ii],cmap=cmap,norm=norm)
    # title=visualizers.animatedTitle(fig, 't=%g ms'%tv[ii])
    # # tbar=tax.barh(0,tv[ii])
    # tbar=tax.vlines(tv[ii],0,1)
    # arts.append([scat,title,tbar])


if vids:
    ani=img.animateStudy('volt-'+strat,fps=30.)
    # erAni=err.animateStudy('error-'+strat,fps=30.)

