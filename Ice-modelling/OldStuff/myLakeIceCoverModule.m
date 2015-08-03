# From the ice cover module of MyLake
# https://github.com/biogeochemistry/MyLake/blob/a08bec0a19cc3c09c468424f41bf84069c197246/v12/v12/solvemodel_v12.m
# lines 265 til 278
# lines 737 to 827



%Initialisation of ice & snow variables
Hi=Ice0(1);               %total ice thickness (initial value, m)
WEQs=(rho_snow/rho_fw)*Ice0(2); %snow water equivalent  (initial value, m)
Hsi=0;                %snow ice thickness (initial value = 0 m)

if ((Hi<=0)&(WEQs>0))
    error('Mismatch in initial ice and snow thicknesses')
end




   else % ice cover module
        XE_surf=(Tz(1)-Tf) * Cw * dz; %Daily heat accumulation into the first water layer (J m-2)
        Tz(1)=Tf; %Ensure that temperature of the first water layer is kept at freezing point
        TKE=0; %No energy for wind mixing under ice

      if (Wt(i,3)<Tf) %if air temperature is below freezing
         %Calculate ice surface temperature (Tice)
         if(WEQs==0) %if no snow
          alfa=1/(10*Hi);
          dHsi=0;
         else
          K_snow=2.22362*(rho_snow/1000)^1.885; %Yen (1981)
          alfa=(K_ice/K_snow)*(((rho_fw/rho_snow)*WEQs)/Hi);
          %Slush/snow ice formation (directly to ice)
          dHsi=max([0, Hi*(rho_ice/rho_fw-1)+WEQs]);
          Hsi=Hsi+dHsi;
         end
       Tice=(alfa*Tf+Wt(i,3))/(1+alfa);

        %Ice growth by Stefan's law
       Hi_new=sqrt((Hi+dHsi)^2+(2*K_ice/(rho_ice*L_ice))*(24*60*60)*(Tf-Tice));
        %snow fall
       dWEQnews=0.001*Wt(i,7); %mm->m
       dWEQs=dWEQnews-dHsi*(rho_ice/rho_fw); % new precipitation minus snow-to-snowice in snow water equivalent
       dHsi=0; %reset new snow ice formation
      else %if air temperature is NOT below freezing
        Tice=Tf;    %ice surface at freezing point
        dWEQnews=0; %No new snow
        if (WEQs>0)
        %snow melting in water equivalents
        dWEQs=-max([0, (60*60*24)*(((1-IceSnowAttCoeff)*Qsw)+Qlw+Qsl)/(rho_fw*L_ice)]);
                if ((WEQs+dWEQs)<0) %if more than all snow melts...
                Hi_new=Hi+(WEQs+dWEQs)*(rho_fw/rho_ice); %...take the excess melting from ice thickness
                else
                Hi_new=Hi; %ice does not melt until snow is melted away
                end
        else
        %total ice melting
        dWEQs=0;
        Hi_new=Hi-max([0, (60*60*24)*(((1-IceSnowAttCoeff)*Qsw)+Qlw+Qsl)/(rho_ice*L_ice)]);
        %snow ice part melting
        Hsi=Hsi-max([0, (60*60*24)*(((1-IceSnowAttCoeff)*Qsw)+Qlw+Qsl)/(rho_ice*L_ice)]);
            if (Hsi<=0)
                Hsi=0;
            end
        end %if there is snow or not
      end %if air temperature is or isn't below freezing


      %Update ice and snow thicknesses
      Hi=Hi_new-(XE_surf/(rho_ice*L_ice)); %new ice thickness (minus melting due to heat flux from water)
      XE_surf=0; %reset energy flux from water to ice (J m-2 per day)
      WEQs=WEQs+dWEQs; %new snow water equivalent

      if(Hi<Hsi)
          Hsi=max(0,Hi);    %to ensure that snow ice thickness does not exceed ice thickness
                            %(if e.g. much ice melting much from bottom)
      end


      if(WEQs<=0)
       WEQs=0; %excess melt energy already transferred to ice above
       rho_snow=rho_new_snow;
      else
       %Update snow density as weighed average of old and new snow densities
       rho_snow=rho_snow*(WEQs-dWEQnews)/WEQs + rho_new_snow*dWEQnews/WEQs;
         if (snow_compaction_switch==1)
         %snow compaction
           if (Wt(i,3)<Tf) %if air temperature is below freezing
           rhos=1e-3*rho_snow; %from kg/m3 to g/cm3
           delta_rhos=24*rhos*C1*(0.5*WEQs)*exp(-C2*rhos)*exp(-0.08*(Tf-0.5*(Tice+Wt(i,3))));
           rho_snow=min([rho_snow+1e+3*delta_rhos, max_rho_snow]);  %from g/cm3 back to kg/m3
           else
           rho_snow=max_rho_snow;
           end
         end
      end

      if(Hi<=0)
      IceIndicator=0;
      disp(['Ice-off, ' datestr(datenum(M_start)+i-1)])
      XE_melt=(-Hi-(WEQs*rho_fw/rho_ice))*rho_ice*L_ice/(24*60*60);
             %(W m-2) snow part is in case ice has melted from bottom leaving some snow on top (reducing XE_melt)
      Hi=0;
      WEQs=0;
      Tice=NaN;
      DoM(pp)=i;
      pp=pp+1;
      end

   end %of ice cover module